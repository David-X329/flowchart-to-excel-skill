---
name: flowchart-to-excel
description: |
  Extract flowchart data from images into structured Excel/Feishu Sheet files. Use when user provides a flowchart image (process flow, workflow diagram) and asks to convert it into a spreadsheet with columns: L4, System, Role, Auto, L5.

  Triggers include requests like: "extract this flowchart to Excel", "convert process diagram to spreadsheet", "识别流程图并生成excel", "把流程图片整理进excel文件".

  Supports complex flowcharts with multiple rows and columns of step cards.
---

# Flowchart → Structured Table Extraction

Extract structured data from flowchart images into Feishu Sheet (preferred) or Excel (`.xlsx`) with 5 columns: L4, System, Role, Auto, L5.

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

## 🔑 Role Value Determination (Priority Order) — 严格遵守！

### 规则（5级优先级）
1. **卡片外左上方的文字标签（External Labels）** — 最高优先级
   - OCR扫描范围：`x-90 ~ x+15, y-28 ~ y+3`（卡片左上角外侧约105×31px区域）
   - 对每个卡片独立扫描，不同卡片可能有标签也可能没有
   - 使用 `--psm 7 --oem 3` 进行单行OCR

2. **泳道左侧的竖排/横排文字标签（Left-Side Lane Labels）** — 次优先级
   - 扫描范围：`x=0 ~ x=160`，y 步进 10-20px
   - 将卡片按 y 坐标分组到对应泳道，泳道内所有卡片继承该泳道标签
   - 适用于卡片左上外侧无独立标签的情况

3. **卡片 y 坐标泳道推断** — 同一 y 范围内无标签的卡片，继承同泳道其他卡片的角色

4. **内容推理** — 前三种都没有时，从卡片内容推断，并添加标注

5. **无法确定** — 标记为 "TBD" 等待用户修正

### 典型角色标签示例
| OCR 片段 | 实际角色 | 说明 |
|---------|---------|------|
| "O5t3 ae" / "Cats Fears" | Developer/Operator | 小字低对比度时常见乱码 |
| "Oe Foye" / "Oe Fours" | Developer/Operator | 常见重复乱码标签 |
| "886 7C" | SSG HC | 数字+字母组合可能为角色缩写 |
| "TT" | IT | 缩写形式 |
| "Business co/stk" | Business | 截断文本 |
| "Request" | Requestor | 缩写形式 |

### 常见错误（⚠️ 必须避免）
- ❌ 不要自作聪明推断Role名称
- ❌ 不要用卡片主标题的文字去猜Role
- ❌ 不要把所有卡片统一给同一个Role（除非泳道标签明确）
- ✅ 严格按照： **卡片左上外侧标签 → 泳道左侧标签 → 同泳道继承 → 推理（标注）→ TBD**

## 🔑 Column Value Rules

### System 列 — 🔑 关键规则更新（2026-05-25）

#### 规则1：卡片正下方的文字 = System（⚠️ 最高优先级）
- **系统文字位于卡片正下方、卡片外、紧贴卡片底部**
- **不是卡片内部**的文字，而是卡片外相邻的文字
- OCR 扫描范围：卡片底部 `y2+2 ~ y2+35`
- 检测方法：逐行扫描底部区域，找到连续暗像素行（阈值：row dark pixels > 12），对该区域进行 `--psm 7/8` OCR
- **只有卡片正下方有清晰文字时才填入系统名；否则填"Offline"**

#### 规则2：泳道左侧标签 = System 兜底（⚠️ 第二优先级）
- 当卡片下方文字乱码/不可读时，使用该卡片所在泳道的**左侧标签**作为 System
- 适用于同一泳道内所有卡片共用一个系统名的情况
- 左侧标签扫描范围：`x=0 ~ x=160`，按 y 区间分组

#### 规则3：判断标准
- 卡片下方有清晰可读文字 → 填入该系统名（优先于泳道标签）
- 卡片下方有乱码片段（如 "PECC", "ated", "Sateiell", "23r", "Ste", "er"）→ 尝试解读，若无法确定→"Offline"
- 卡片下方无任何文字（dark pixel total < 18）→ "Offline"
- 卡片下方有分隔线 "—————" → 装饰线，不是系统名 → "Offline"

#### 常见乱码 → 可能系统名
| 乱码 | 可能系统 |
|------|---------|
| "PECC" / "ated" / "Sateiell" | SAP ECC |
| "23r" / "Pp" / "val" | BPC / Power BI |
| "Seesttep" / "Pastor" | 无法确定→Offline |

#### ⚠️ 重要
- 如果卡片内本身提到了系统名（如 "Login to Power BI"）→ 这是卡片内容，不是 System 列
- System 列只看卡片**下方外部文字**和**泳道标签**，不看卡片内部文字

### L5 列
- 填入卡片内的**全部可见文字**
- **不要留空** — 如果OCR读不到完整内容，填入卡片标题文本作为兜底
- 完整格式应为：卡片标题 + 卡片内其他描述文字

### Ordering
- 排序完成后，按照排序顺序输出到Sheet（序号1=第一行）

## Output Format

### Feishu Sheet (Preferred)
- Create via Feishu API: `POST https://open.feishu.cn/open-apis/sheets/v3/spreadsheets`
- Fill data via: `PUT https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{token}/values`
- Header row: L4, System, Role, Auto, L5
- Each flowchart image = its own new sheet document (do NOT append to existing docs)
- Grant `full_access` to the user's Feishu ID

### Column Mapping

| Column | Name | Content Rule |
|--------|------|-------------|
| A | **L4** | Card step name/title (第一行文案，清洗后) |
| B | **System** | 系统名称；未识别到→"Offline" |
| C | **Role** | Role determined per priority logic above |
| D | **Auto** | Auto/Manual/User/(empty) based on icon analysis |
| E | **L5** | 卡片全部文字；不得留空 |

**Color coding for Auto column:**
- `Auto` → Green - automated step
- `Manual` → Red - manual step  
- `User` → Yellow - user action required
- (empty) → No fill

## Connected-Component Card Detection (Recommended)

使用连通域分析替代逐行扫描，更准确地检测蓝色卡片：

```python
# 1. 创建蓝色掩码
blue_mask = np.zeros((h, w), dtype=np.uint8)
for y in range(h):
    for x in range(w):
        if is_blue(pixels[y,x]): blue_mask[y, x] = 255

# 2. BFS/DFS 连通域检测
visited = np.zeros((h, w), dtype=bool)
for y in range(0, h):
    for x in range(0, w):
        if blue_mask[y, x] == 255 and not visited[y, x]:
            # BFS flood fill to find bounding box
            # Filter: width >= 70, height >= 25

# 3. 排序
cards.sort(key=lambda c: (c['x1'], c['y1']))  # X 优先，Y 其次
```

## Auto/Manual Icon Detection (Center-Density Method)

```python
# 裁剪卡片左上角 ~55% height × 35% width 区域
ir = card_pixels[:int(h*0.55), :int(w*0.35)]
# 检测白色像素（r>200, g>200, b>200）
white_count = np.sum(white_mask)
# 检测中心密度（~6×6px 中心区域）
center_region = ir[center_y-3:center_y+3, center_x-3:center_x+3]
center_density = np.sum(center_white) / max(area, 1)

# 判定
if white_count > 5 and center_density > 0.06:
    icon = "Manual"  # 手形：中心实心
elif white_count > 5:
    icon = "Auto"    # 齿轮：中心空心
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

## OCR Accuracy Notes

- OCR on colored flowchart cards (white text on blue background) is imprecise
- Common garbled results: CAN→CAH/CARN, Submit→Subrnil, Create→Creale, etc.
- **Always review output** and manually correct garbled text when possible
- The user (client/manager) can provide corrections verbally
- If OCR quality is too poor to read card text, the user can provide card names verbally — always defer to user's corrections

## Output Conventions

### Excel Format (openpyxl)
- Header: dark blue (#1F4E79) with white text
- Auto column: green (#C6EFCE) for Auto, red (#FFC7CE) for Manual
- Frozen header row, auto-filter enabled
- Column widths: L4=40, System=12, Role=14, Auto=10, L5=40
- File naming: `flowchart_output{N}.xlsx` (递增编号)

### Voice Confirmation
- 使用 edge-tts 发送语音确认
- 声音：`zh-CN-YunxiNeural`（首选，十五岁男孩声音），失败时回落 `zh-CN-XiaoxiaoNeural`（女声）
- 常见失败：YunxiNeural 可能返回 "NoAudioReceived" 或 SIGKILL
- 语音内容：简要概括步骤数、流程名、Role 数量和 Auto/Manual 分布

## Dependencies

- Python: `Pillow`, `numpy`, `pytesseract`, `openpyxl`
- System: `tesseract` with `eng` language data
- Voice: `edge-tts` (via `~/.openclaw/workspace/skills/edge-tts-feishu/bin/edge-tts-to-feishu`)

## 经验总结（2026-05-25）

### 已验证的处理数量
截至 2026-05-25，已成功处理 **14 张流程图**（flowchart_output ~ output13），涵盖：
- COA Request（25卡）、COA Maintenance（14卡）、Bank Reconciliation（6卡+11卡）
- GL-SL Reconciliation（9卡）、Financial Reporting（6卡）、Audit（15卡）
- Corporate Income Tax（9卡）、Forecast（8卡）、Internal Audit（7卡）
- SR Workflow（13卡）、Power BI Dashboard（5卡）、MBR Forecast（12卡）

### 关键教训
1. **蓝色检测阈值至关重要**：过于严格会导致漏检浅蓝色卡片
2. **System 列只看卡片下方和泳道标签**：绝对不看卡片内部文字
3. **外部角色标签可能严重乱码**：小字体低对比度时 OCR 几乎不可靠，需要泳道标签兜底
4. **连通域检测优于逐行扫描**：不会漏掉任意位置的卡片
5. **YunxiNeural 声音不稳定**：准备好 XiaoxiaoNeural 回落
6. **用户随时可修正**：Role/System 标错时等用户反馈再改

## License
MIT
