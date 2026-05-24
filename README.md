# Flowchart → Excel Skill 🖼️→📊

**An AI Agent skill that extracts structured data from flowchart images into Excel files.**

Ideal for: business analysts, process engineers, and anyone who needs to convert process flow diagrams into structured data.

## Features

- 🧠 **Smart OCR** — Preprocesses images (contrast + sharpening) for accurate text recognition
- 🃏 **step card extraction** — Parses grid flowcharts
- 🏷️ **Role recognition** — 20+ known role keywords + context inference engine
- 🔗 **System detection** — Auto-detects system names from card bottom
- 📊 **Excel output** — Clean, formatted `.xlsx` with L4/System/Role/L5 columns
- 🤖 **Agent-ready** — Works with OpenClaw, custom agents, and CLI

## Quick Start

```bash
# Install
pip install Pillow pytesseract openpyxl

# Run
python3 scripts/flowchart_to_excel.py my_flowchart.png output.xlsx
```

## For AI Agents (OpenClaw)

Add to your `openclaw.yaml`:

```yaml
skills:
  - name: flowchart-to-excel
    git: https://github.com/David-X329/flowchart-to-excel-skill.git
    branch: main
```

Then say: *"提取这个流程图的表格数据"* or *"Convert this flowchart to Excel"*

## Output Example

| L4 | System | Role | L5 |
|---|---|---|---|
| Receive Customer Complaint | CRM | Customer Service Rep | Receive customer complaint via email... |
| Validate Complaint Details | CRM | Validator / QC (Suggest to check) | CSM validates complaint details... |
| ... | ... | ... | ... |

## Dependencies

- Python 3.8+
- Tesseract OCR (system-level, [install guide](https://github.com/tesseract-ocr/tesseract))

## Related Projects

- [Flowchart2Excel Desktop App](https://github.com/David-X329/flowchart2excel) — Windows GUI version with multi-step wizard

## License

MIT
