---
name: flowchart-to-excel
description: |
  Extract flowchart data from images into structured Excel files. Use when user provides a flowchart image (process flow, workflow diagram) and asks to convert it into an Excel spreadsheet with columns: L4, System, Role, Auto, L5.

  Triggers include requests like: "extract this flowchart to Excel", "convert process diagram to spreadsheet", "识别流程图并生成excel", "把流程图片整理进excel文件".

  Supported layout: cards arranged in a 2-row × 3-column grid (flowchart), with a left-side lane (x≈86-310) containing role labels, and connector lanes between columns.
---

# Flowchart → Excel Extraction

Extract structured data from flowchart images into Excel (`.xlsx`) with 5 columns: L4, System, Role, Auto, L5.

## Icon-to-Auto Mapping (Critical)

Each card has a small icon at the top-left corner. The icon determines the **Auto** column value:

| Icon | Shape | Auto Value |
|------|-------|-----------|
| ⚙️ Gear (hollow center ring) | `Auto` |
| ✋ Hand (solid shape, finger-like protrusions) | `Manual` |
| 👤 Person (head + shoulders/body) | `User` |
| ❌ No icon / blank area | (leave empty) |

**Icon identification techniques:**
1. Crop ~38×38 pixel region at card top-left
2. Threshold to isolate icon pixels (white-on-blue-background)
3. Check center density: hollow (gear) ≈ 0, solid (hand/person) > 0
4. Check shape: gear has hole in center, person has "head" bump, hand has finger-like protrusions
5. Always zoom 4-8× for visual confirmation
6. When in doubt, compare multiple icon images side-by-side

## Role Value Logic (Priority Order)

1. **Card top-left corner label** → Use directly (highest priority)
2. **Left-side lane label** → Use the lane's role label for that row
3. **Content inference** → If neither above → append "(need to check)" after inferred role

## Output Columns

| Column | Name | Content Rule |
|--------|------|-------------|
| A | **L4** | Card title text (main heading from card content) |
| B | **System** | System name from card text (e.g. Service Connect, BRIM, ESOT, BRIM CM) |
| C | **Role** | Role determined per priority logic above |
| D | **Auto** | Auto/Manual/User/(empty) based on icon analysis |
| E | **L5** | Full step description (card main body text) |

## Excel Format (Reference Template)

```
Row 1: Merged title "Flowchart - [Process Name] (Sheet 1 of N)"
Row 2: Headers | L4 | System | Role | Auto | L5 |
Row 3+: Data rows (exactly 6 rows for one flowchart = 2×3 card grid)
```

**Color coding for Auto column:**
- `Auto` → Green fill (C6EFCE)
- `Manual` → Red fill (FFC7CE)
- `User` → Yellow fill (FFEB9C)
- (empty) → No fill

**Critical rules:**
- **Do NOT add extra rows.** One flowchart image = exactly 6 data rows (one per card)
- **Do NOT hallucinate text.** Use only text that appears in the card
- **Do NOT merge cards.** Each card is one row, in natural order (left→right, top→bottom)
- If a second image is another page of the same process, it is NOT additional steps — use it only to clarify/correct the first 6 rows

## Extraction Process

1. **Load image** → Convert to RGB if RGBA
2. **Preprocess** → Convert to grayscale, threshold for OCR
3. **OCR** → Use `pytesseract` with image_to_data() for position-aware text extraction
4. **Map to cards** → Group text by card region coordinates
5. **Extract fields:**
   - **L4 (Card Title)**: Main heading from card
   - **System**: System name from card text
   - **Role**: Per priority logic; if card top-left has explicit label → use it. If from lane → note. If inferred → add "(need to check)"
   - **Auto**: Icon analysis per table above
   - **L5**: Full card body text

### OCR Accuracy Note

OCR on colored flowchart cards can be imprecise. Always **review output** and manually correct garbled text.

## Dependencies

- Python: `Pillow`, `pytesseract`, `openpyxl`
- System: `tesseract` with `eng` language data

## License

MIT
