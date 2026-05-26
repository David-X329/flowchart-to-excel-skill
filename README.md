# BOx Flowchart → Excel Skill 🖼️→📊

**An AI Agent skill that extracts structured data from flowchart images into Excel files.**

Ideal for: business analysts, process engineers, and anyone who needs to convert process flow diagrams (swimlane, grid, or hybrid layouts) into structured spreadsheets.

## Features

- 🧠 **Smart OCR** — Preprocesses images (contrast + sharpening) for accurate text recognition
- 🃏 **Flexible card detection** — Handles any number of cards in swimlane or grid layouts
- 🔵 **Blue card auto-detection** — Finds step cards by color (b>r+30, b>g+30, b>100)
- 🏷️ **Role recognition** — 5-level priority: external labels → lane labels → same-lane inheritance
- ⚙️ **Auto/Manual detection** — Identifies automation status via icon analysis (gear/manual)
- 📊 **Excel output** — Clean, formatted `.xlsx` with **Step | System | Role | Automated or Manual | Activity** columns
- 🤖 **Agent-ready** — Works with OpenClaw, custom agents, CLI, and REST API

## Quick Start

```bash
# Install
pip install Pillow pytesseract openpyxl numpy

# Run pipeline
python3 scripts/flowchart_pipeline.py my_flowchart.png output.xlsx
```

## For AI Agents (OpenClaw)

Add to your `openclaw.yaml`:

```yaml
skills:
  - name: flowchart-to-excel
    git: https://github.com/David-X329/flowchart-to-excel-skill.git
    branch: main
```

Then say: *"read this flowchart"* or *"Convert this flowchart to Excel"*

## Output Example

| Step | System | Role | Automated or Manual | Activity |
|---|---|---|---|---|
| Loading Forecast in BPC | SAP BPC | Finance | Manual | Loading Forecast in BPC |
| Update dashboards | Power BI | — | Auto | Update dashboards |
| Send Prepopulated Deck | CRM | Operation | Manual | Send Prepopulated Deck |
| ... | ... | ... | ... | ... |

## REST API

```bash
# Start server
python3 api.py

# Process an image
curl -X POST http://localhost:5000/process \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "'$(base64 -i flowchart.png)'"}'
```

## Dependencies

- Python 3.8+
- Tesseract OCR (system-level, [install guide](https://github.com/tesseract-ocr/tesseract))

## Related Projects

- [Flowchart2Excel Desktop App](https://github.com/David-X329/flowchart2excel) — Windows GUI version with multi-step wizard

## License

MIT

