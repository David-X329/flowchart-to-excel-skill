---
name: flowchart-to-excel
description: |
  Extract flowchart data from images into structured Excel files. Use when user provides a flowchart image (process flow, workflow diagram) and asks to convert it into an Excel spreadsheet with columns: L4, System, Role, L5.

  Triggers include requests like: "extract this flowchart to Excel", "convert process diagram to spreadsheet", "识别流程图并生成excel", "把流程图片整理进excel文件".

  Supported flowchart layout: cards arranged in a 2-row × 3-column grid with a left-side lane (x≈86-310) containing role labels, and connector lanes between columns.
---

# Flowchart → Excel Extraction

Extract structured data from flowchart images into Excel (`.xlsx`).

## Installation

### Prerequisites

- Python 3.8+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed on your system

### Install

```bash
# Install Python dependencies
pip install Pillow pytesseract openpyxl
```

### Clone the skill

```bash
git clone https://github.com/David-X329/flowchart-to-excel-skill.git
cd flowchart-to-excel-skill
```

Or download the ZIP from the [GitHub releases page](https://github.com/David-X329/flowchart-to-excel-skill/releases).

## Usage

### Command line

```bash
python3 scripts/flowchart_to_excel.py <image_path> [output_path]
```

Example:
```bash
python3 scripts/flowchart_to_excel.py my_flowchart.png result.xlsx
```

### As a library in your own code

```python
from scripts.flowchart_to_excel import extract_flowchart

cards = extract_flowchart("flowchart.png")
for card in cards:
    print(f"L4: {card['L4']}")
    print(f"System: {card['System']}")
    print(f"Role: {card['Role']}")
    print(f"L5: {card['L5']}")
```

### For OpenClaw / AI Agent users

Add to your `openclaw.yaml`:

```yaml
skills:
  - name: flowchart-to-excel
    git: https://github.com/David-X329/flowchart-to-excel-skill.git
    branch: main
```

Then trigger the skill with natural language like:
- "Extract this flowchart to Excel"
- "Convert this process diagram to a spreadsheet"
- "识别这个流程图并生成Excel文件"

## Supported Layout

The tool expects a specific flowchart layout:
- **Title**: Centered at top ("Invoice to Cash" or similar)
- **Cards**: Arranged in 2 rows × 3 columns
  - Row 1 (top): y≈130-212
  - Row 2 (bottom): y≈245-330
  - Col 1: x≈310-430, Col 2: x≈490-610, Col 3: x≈670-790
- **Left Lane** (x≈86-310): Contains per-row role labels / connector info
- **Connector Lanes** (between columns): Flow arrows with step numbers

## Output Columns

| Column | Name | Content Rule |
|--------|------|-------------|
| A | **L4** | Step name / title (from card main content) |
| B | **System** | System name from card bottom area; if empty → "offline" |
| C | **Role** | Role from card content; if card explicitly mentions a role → fill it; if inferred from step context → append "(Suggest to check)" |
| D | **L5** | Full step description (from card main content) |

## Extraction Process

1. **Load image** → Convert to RGB if RGBA
2. **Preprocess** → Convert to grayscale, threshold (pixel < 200 → 0)
3. **OCR** → Use `pytesseract` with image_to_data() for position-aware text extraction
4. **Map to cards** → Group text by card region coordinates
5. **Extract fields** with smart logic:
   - **L4**: Step name from dominant card text
   - **System**: Bottom text → "offline" if empty
   - **Role**: Keywords matching + context inference
   - **L5**: Full descriptive text

### OCR Accuracy Note

OCR on colored flowchart cards can be imprecise. After running the script, **always review** and manually correct:
- **L4/L5**: Clean up garbled OCR text (e.g. "colect" → "collect", "dala" → "data")
- **System**: Verify the system name matches the card bottom text
- **Role**: Ensure role rule above is applied correctly

## Dependencies

- Python: `Pillow`, `pytesseract`, `openpyxl`
- System: `tesseract` with `eng` language data

## License

MIT
