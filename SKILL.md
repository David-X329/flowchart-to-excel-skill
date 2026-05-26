---
name: BOx-flowchart-to-excel
description: |
  Extract flowchart data from images into structured Excel/Feishu Sheet files. Use when user provides a flowchart image (process flow, workflow diagram) and asks to convert it into a spreadsheet with columns: Step, System, Role, Automated or Manual, Activity.

  Triggers include requests like: "extract this flowchart to Excel", "convert process diagram to spreadsheet", "识别流程图并生成excel", "把流程图片整理进excel文件".

  Supports complex flowcharts with multiple rows and columns of step cards.
---

# Flowchart → Structured Table Extraction

Extract structured data from flowchart images into Excel (`.xlsx`) with 5 columns: Step, System, Role, Automated or Manual, Activity.

## Step Card Definition

**Step cards** are **blue rectangles** filled with blue color ~RGB(6, 124, 193) containing white text. Each step card represents a single step in the process.

**Color detection condition:** `b > r+60 AND g > r+60 AND b > g+30` (for RGB images)
- This relaxed threshold catches lighter blue cards that still have distinct blue tint

**Typical card dimensions:**
- Width: 70–150px (standard card)
- Height: 25–80px (standard card)
- Minimum detection threshold: width ≥ 70px, height ≥ 25px
- Blue fill is continuous across the card area

### Non-card elements to skip

| Element | Appearance | Reason |
|---------|-----------|--------|
| Decision diamonds | Diamond/rhombus shape, white/light background | No step number |
| Note/annotation boxes | Small text blocks (<40px height), no blue fill | No step number |
| Lane title/label bars | Wide blue rectangle (>150px), at row start | No step number |
| Arrow connector labels | Small text on connector lines | Not a card |
| Non-blue / non-grid text labels | Text in card-like position (same x spacing as cards) but no blue fill, e.g. "Approval received" | Not a step card — textual annotation |

## Step Number Detection & Ordering

### Number Location
Each step card has a **small black digit number** just **outside the card rectangle** in the **top-left corner area** (above or to the left of the card). The number is NOT inside the card.

### Number Characteristics
- Very small black digits (typically 6-10pt, ~8-12px tall in source image)
- Located in the region: 20-40px left and 20-35px above the card's top-left corner
- May also appear inside small grey/dark circles (RGB ~42-60) on connector arrows between cards
- **Extremely hard for OCR to read** — numbers may be only a few pixels wide in the source image

### Ordering Rules (Priority)

1. **If step numbers are readable**: Sort by step number ascending (1, 2, 3... N)
   - Step number trumps physical position entirely
   - Numbering is continuous 1-N with no gaps

2. **If step numbers are NOT readable by OCR**: Sort by physical position using this strict priority:
   - **Primary: Column (X position)** — left-to-right
   - **Secondary: Row (Y position)** — top-to-bottom
   - This means cards on the left side of the flowchart come first, regardless of which row/lane they're in
   - Different swim lanes' cards will be **interleaved** if they share the same X range

3. **Unnumbered step cards**: Any blue rectangle that is a step card but lacks a step number is placed **after all numbered cards** (at the bottom of the list)

4. **Never guess** the step number value. If OCR can't read the small black text, fall back to physical position sorting (#2 above).

## Card Detection Algorithm

### Step 1: Find Blue Rows
```python
# Scan every 3rd pixel row
for y in range(0, h, 3):
    blue_count = count_blue_pixels_at_y(y)  # sample every 15th x
    if blue_count > 3:
        record this y as containing blue

# Group consecutive blue y-values into bands
# Gap threshold: 6px between bands
# Minimum band height: 40px (smaller bands = annotations/diamonds, skip)
```

### Step 2: Find Cards Within Each Row
```python
for each row (y1, y2):
    y_mid = (y1 + y2) // 2
    scan x from 0 to w:
        if pixel at (x, y_mid) is blue fill → card start
        if pixel stops being blue for >3px → card end
    filter: only cards with width 70-120px are standard step cards
```

### Step 3: Identify Non-Card Elements
- Width > 150px → lane label/title bar (skip)
- Height < 40px → annotation/decision element (skip)

### ⚠️ Card Detection Across Multiple Vertical Bands

Cards in the same swim lane may span **multiple vertical blue bands** (different y-ranges).
For example, a swim lane might have cards at y=134-205 AND cards at y=254-325 that
belong to the same lane. Always check **all** blue bands in the image when counting cards.

**Complete scan approach:**
1. Find ALL blue bands (y ranges) in the image
2. For each band, find all standard-width (70-120px) blue rectangles
3. Group cards by swim lane (use separator lines / left-side lane labels)
4. Use X position + user input to determine correct lane assignment

### Step 4: Read Card Text
```python
for each card region (x1, y1, x2, y2):
    crop card with 2px margin
    extract white text pixels (r>200, g>200, b>200)
    create 4x zoomed inverted image (white bg, black text)
    OCR with pytesseract (--psm 6 --oem 3, lang=eng)
    clean garbled OCR output
```

## Auto/Manual/User Detection (from Card Icons)

Each card has a **small icon** at its **top-left corner** (~38×38px region). The icon type determines the Auto column value:

| Icon | Visual Features | Auto Value |
|------|----------------|-----------|
| ⚙️ **Gear** | Hollow center ring, toothed outer edge | `Auto` |
| ✋ **Hand** | Solid shape, finger-like protrusions | `Manual` |
| 👤 **Person** | Head bump + shoulders/body outline | `User` |
| ❌ **No icon** | Blank/empty top-left corner | (leave empty) |

**Detection technique:**
1. Crop ~38×38 pixel region at card top-left corner (x+2, y+2)
2. Extract white pixels from blue background
3. Analyze center density: gear has hollow center (density ≈ 0), hand/person is solid
4. Analyze shape outline: gear has teeth, hand has fingers, person has head bump
5. Zoom 4-8× for visual confirmation when uncertain

## 🔑 Role Value Determination (5-Level Priority)

### Rules (Strict Priority Order)
1. **External Labels (above-left of card)** — Highest priority
   - OCR scan region: `x-90 to x+15, y-28 to y+3` (~105×31px area outside top-left of card)
   - Scan each card independently; different cards may or may not have labels
   - Use `--psm 7 --oem 3` for single-line OCR

2. **Left-side Lane Labels** — Second priority
   - Scan region: `x=0 to x=160`, y step 10-20px
   - Group cards by y-coordinate into lanes; all cards in a lane inherit the lane's label
   - Use when no external label exists above-left of card

3. **Same-Lane Inheritance** — Cards in the same y-range without labels inherit the role from other labeled cards in the same lane

4. **Content Inference** — When none of the above apply, infer from card content and annotate with "(need to check)"

5. **Unknown** — Mark as "TBD" and await user correction

### Typical Garbled Label → Actual Role Mapping
| OCR Fragment | Actual Role | Notes |
|-------------|-------------|-------|
| "O5t3 ae" / "Cats Fears" | Developer/Operator | Common garbling with small low-contrast text |
| "Oe Foye" / "Oe Fours" | Developer/Operator | Frequently repeated garbled label pattern |
| "886 7C" | SSG HC | Digit+letter combo may be role abbreviation |
| "TT" | IT | Abbreviation |
| "Business co/stk" | Business | Truncated text |
| "Request" | Requestor | Abbreviated form |

### Common Mistakes (⚠️ Must Avoid)
- ❌ Do not guess/invent role names
- ❌ Do not use the card's main title text to guess the role
- ❌ Do not assign the same role to all cards (unless lane labels clearly indicate it)
- ✅ Strictly follow: **External label → Lane label → Same-lane inheritance → Inference (annotated) → TBD**

## 🔑 Column Value Rules

### System Column — Critical Rules (updated 2026-05-25)

#### Rule 1: Text directly below card = System (⚠️ Highest Priority)
- **System text is located directly below the card, outside the card, adjacent to its bottom edge**
- **NOT inside the card** — text outside and adjacent to the card
- OCR scan region: card bottom `y2+2 to y2+35`
- Detection method: scan rows below card bottom, find consecutive dark-pixel rows (threshold: row dark pixels > 12), OCR the region with `--psm 7/8`
- **Only fill in system name when clear readable text exists below card; otherwise use "Offline"**

#### Rule 2: Lane-side labels = System fallback (⚠️ Second Priority)
- When text below card is garbled/unreadable, use the card's **left-side lane label** as System
- Applies when all cards in the same lane share a system name
- Lane label scan region: `x=0 to x=160`, grouped by y-range

#### Rule 3: Judgment Criteria
- Clear readable text below card → Use that system name (priority over lane label)
- Garbled fragments below card (e.g. "PECC", "ated", "Sateiell", "23r", "Ste", "er") → Try to interpret; if uncertain → "Offline"
- No text below card (dark pixel total < 18) → "Offline"
- Separator line "—————" below card → Decorative line, not system name → "Offline"

#### Common Garbled → Possible System Name
| Garbled | Possible System |
|---------|----------------|
| "PECC" / "ated" / "Sateiell" | SAP ECC |
| "23r" / "Pp" / "val" | BPC / Power BI |
| "Seesttep" / "Pastor" | Cannot determine → Offline |

#### ⚠️ Important
- If the card text itself mentions a system name (e.g. "Login to Power BI") → This is card content, NOT the System column
- System column only looks at **text below card** and **lane labels**, never card internal text

### Activity Column
- Enter **all visible text** from within the card
- **Never leave empty** — if OCR cannot read full content, use card title text as fallback
- Full format: card title + any additional description text inside the card

### Ordering
- Output to sheet in sort order (row 1 = first card)

## Connected-Component Card Detection (Recommended)

Use connected-component analysis instead of row-by-row scanning for more accurate blue card detection:

```python
# 1. Create blue pixel mask
blue_mask = np.zeros((h, w), dtype=np.uint8)
for y in range(h):
    for x in range(w):
        if is_blue(pixels[y,x]): blue_mask[y, x] = 255

# 2. BFS/DFS connected-component detection
visited = np.zeros((h, w), dtype=bool)
for y in range(0, h):
    for x in range(0, w):
        if blue_mask[y, x] == 255 and not visited[y, x]:
            # BFS flood fill to find bounding box
            # Filter: width >= 70, height >= 25

# 3. Sort cards
cards.sort(key=lambda c: (c['x1'], c['y1']))  # X first, Y second
```

## Auto/Manual Icon Detection (Center-Density Method)

```python
# Crop top-left ~55% height × 35% width region of card
ir = card_pixels[:int(h*0.55), :int(w*0.35)]
# Detect white pixels (r>200, g>200, b>200)
white_count = np.sum(white_mask)
# Detect center density (~6×6px center region)
center_region = ir[center_y-3:center_y+3, center_x-3:center_x+3]
center_density = np.sum(center_white) / max(area, 1)

# Classification
if white_count > 5 and center_density > 0.06:
    icon = "Manual"  # Hand icon: solid center
elif white_count > 5:
    icon = "Auto"    # Gear icon: hollow center
else:
    icon = "None"
```

## Complete Workflow

1. **Load image** → Convert RGBA to RGB if needed
2. **Detect cards** → Connected-component analysis on blue mask (min 70×25px)
3. **Read card text** → White text extraction + zoomed OCR (try multiple thresholds: 150, 170, 190)
4. **Detect icons** → Center-density method (Manual if center density > 6%)
5. **Read external role labels** → OCR region x-90 to x+15, y-28 to y+3 per card (`--psm 7`)
6. **Read left-side lane labels** → OCR x=0-160, y step 10-20 (`--psm 6`)
7. **Read system text below** → OCR region y2+2 to y2+35, dark-pixel scan (`--psm 7/8`)
8. **Determine roles** → External label → Lane label → Same-lane inheritance → Inference → TBD
9. **Determine System** → Below-card text → Lane label → "Offline"
10. **Sort cards** → By X then Y position (left-to-right, top-to-bottom)
11. **Output xlsx** → openpyxl with header, formatting, frozen pane, auto-filter
12. **Send via media** → Voice confirmation + file attachment

## Output Conventions

### Excel Format (openpyxl)
- Header: dark blue (#1F4E79) with white text
- Auto column: green (#C6EFCE) for Auto, red (#FFC7CE) for Manual
- Frozen header row, auto-filter enabled
- Header row height: 45px (3× default)
- Column widths: Step=40, System=16, Role=16, Automated or Manual=18, Activity=42
- File naming: `flowchart_output{N}.xlsx` (incremental numbering)

### Voice Confirmation
- Use edge-tts for voice confirmation after processing
- Voice: `zh-CN-YunxiNeural` (preferred, male teen voice), fallback to `zh-CN-XiaoxiaoNeural` (female voice) on failure
- Common failures: YunxiNeural may return "NoAudioReceived" or SIGKILL
- Voice content: briefly summarize step count, flow name, role count, and Auto/Manual distribution

## OCR Accuracy Notes

- OCR on colored flowchart cards (white text on blue background) is imprecise
- Common garbled results: CAN→CAH/CARN, Submit→Subrnil, Create→Creale, etc.
- **Always review output** and manually correct garbled text when possible
- The user (client/manager) can provide corrections verbally
- If OCR quality is too poor to read card text, the user can provide card names verbally — always defer to user's corrections

## Dependencies

- Python: `Pillow`, `numpy`, `pytesseract`, `openpyxl`
- System: `tesseract` with `eng` language data
- Voice: `edge-tts` (via `~/.openclaw/workspace/skills/edge-tts-feishu/bin/edge-tts-to-feishu`)

## Field-Tested Results (2026-05-25)

### Verified Processing Count
As of 2026-05-25, **15 flowcharts** have been successfully processed, covering:
- COA Request (25 cards), COA Maintenance (14 cards), Bank Reconciliation (6+11 cards)
- GL-SL Reconciliation (9 cards), Financial Reporting (6 cards), Audit (15 cards)
- Corporate Income Tax (9 cards), Forecast (8 cards), Internal Audit (7 cards)
- SR Workflow (13 cards), Power BI Dashboard (5 cards), MBR Forecast (12 cards)
- Total: 166+ step cards extracted across 15 flowcharts

### Key Lessons Learned
1. **Blue detection threshold is critical**: Too strict causes missed light-blue cards
2. **System column reads from below-card text and lane labels only**: Never use card internal text
3. **External role labels may be severely garbled**: Small-font low-contrast labels are nearly unreadable by OCR; lane labels are essential fallback
4. **Connected-component detection outperforms row-by-row scanning**: Won't miss cards at any position
5. **YunxiNeural voice is unstable**: Always have XiaoxiaoNeural as fallback
6. **User corrections are always authoritative**: When Role/System is marked incorrectly, wait for user feedback before changing

## Output Format

### Excel (xlsx) via openpyxl
- Header row: Step | System | Role | Automated or Manual | Activity
- Header row height: 45px (3× default row height)
- Each flowchart image = its own new xlsx file (do NOT append to existing files)

### Column Mapping

| Column | Name | Content Rule |
|--------|------|-------------|
| A | **Step** | Card step name/title (first line of text, cleaned) |
| B | **System** | System name; if not identified → "Offline" |
| C | **Role** | Role determined per priority logic above |
| D | **Automated or Manual** | Auto/Manual/User/(empty) based on icon analysis |
| E | **Activity** | All visible card text; never leave empty |

**Color coding for Automated or Manual column:**
- `Auto` → Green - automated step
- `Manual` → Red - manual step  
- `User` → Yellow - user action required
- (empty) → No fill

## License
MIT
