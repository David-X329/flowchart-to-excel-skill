# How to Publish flowchart-to-excel Skill to Microsoft Copilot Studio

## Overview

The `flowchart-to-excel` skill is currently an **OpenClaw AgentSkill** — a markdown file with AI agent instructions. There are two ways to publish it to Copilot Studio:

- **Option A (Simplest)**: Upload SKILL.md as a Knowledge Source → Copilot learns the rules
- **Option B (Full Power)**: Wrap Python pipeline as REST API → Copilot can actually process images

---

## Option A: Upload as Knowledge Source (5 minutes)

This teaches Copilot Studio the flowchart extraction rules. It can answer questions about the methodology but **cannot process images** (no Pillow/tesseract in Copilot).

### Steps

1. **Open Copilot Studio** → Go to https://copilotstudio.microsoft.com
2. **Select your agent** (or create a new one)
3. **Go to Knowledge** tab in the left sidebar
4. **Click "+ Add knowledge"** → Choose **Upload files**
5. **Upload the English SKILL.md** (download from https://github.com/David-X329/flowchart-to-excel-skill/blob/main/SKILL.md)
6. **Save** the agent

### How it works
- Copilot indexes the SKILL.md content
- When users ask about flowchart extraction rules, Copilot retrieves relevant sections
- Example: "How do I detect the System column?" → Copilot answers from the rules

### Limitation
- Copilot can explain the rules but **cannot run the Python code** (no Pillow, tesseract, openpyxl)

---

## Option B: Custom Connector + REST API (Full Automation)

This lets Copilot Studio **actually process flowchart images** by calling a REST API that runs the Python pipeline.

### Architecture

```
Copilot Studio (Agent)
    ↕ Custom Connector (OpenAPI)
        ↕ REST API (Flask/FastAPI on Azure/VM)
            ↕ Python: Pillow + pytesseract + openpyxl
                ↕ Output: Excel file
```

### Step 1: Create the REST API

```python
# flowchart_api.py
from flask import Flask, request, send_file, jsonify
import base64, io, tempfile, os
from flowchart_pipeline import process_flowchart  # your existing code

app = Flask(__name__)

@app.route('/process-flowchart', methods=['POST'])
def process_image():
    """Accept image (base64 or file upload), return xlsx"""
    data = request.json
    if not data or 'image_base64' not in data:
        return jsonify({'error': 'Missing image_base64'}), 400

    # Decode image
    img_bytes = base64.b64decode(data['image_base64'])

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(img_bytes)
        img_path = f.name

    try:
        # Run flowchart pipeline
        output_path = process_flowchart(img_path)
        return send_file(output_path, as_attachment=True,
                        download_name='flowchart_output.xlsx')
    finally:
        os.unlink(img_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Step 2: Create OpenAPI Specification

```yaml
# flowchart-api.yaml
openapi: 3.0.0
info:
  title: Flowchart to Excel API
  description: Extracts structured data from flowchart images
  version: 2.1.0
servers:
  - url: https://your-server.com/api
paths:
  /process-flowchart:
    post:
      summary: Process flowchart image
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                image_base64:
                  type: string
                  description: Base64-encoded PNG/JPEG image
      responses:
        '200':
          description: Excel file
          content:
            application/vnd.openxmlformats-officedocument.spreadsheetml.sheet:
              schema:
                type: string
                format: binary
```

### Step 3: Deploy to Azure

**Option 1: Azure App Service (Easiest)**
```bash
az webapp up --name flowchart-processor --runtime PYTHON:3.11 --sku B1
```

**Option 2: Azure Container Apps**
```bash
docker build -t flowchart-api .
docker tag flowchart-api yourregistry.azurecr.io/flowchart-api:v1
docker push yourregistry.azurecr.io/flowchart-api:v1
az containerapp create --name flowchart-api --image yourregistry.azurecr.io/flowchart-api:v1
```

### Step 4: Register Custom Connector in Power Platform

1. Go to **Power Apps** → https://make.powerapps.com
2. **Custom Connectors** → **+ New custom connector** → **Import an OpenAPI file**
3. Upload `flowchart-api.yaml`
4. Configure authentication (API key recommended)
5. **Test** the connector with a sample image
6. **Create connector**

### Step 5: Add as Tool in Copilot Studio

1. Open your agent in **Copilot Studio**
2. Go to **Tools** tab
3. **+ Add tool** → **Connector** → Select your custom connector
4. Add a description: "Processes flowchart images. When user uploads a flowchart PNG, extracts structured data (L4, System, Role, Auto, L5) into Excel"
5. **Save** and **Publish** the agent

### How it works after setup
1. User uploads flowchart image to Copilot chat
2. Copilot recognizes it's a flowchart → calls the Custom Connector
3. API processes the image with Python pipeline
4. Returns Excel file to the chat

---

## Which Option Should I Choose?

| | Option A (Knowledge) | Option B (API) |
|---|---|---|
| **Setup time** | 5 minutes | 1-2 hours |
| **Actually processes images** | ❌ No | ✅ Yes |
| **Explains rules** | ✅ Yes | ❌ With extra topic |
| **Cost** | Free (Copilot Studio license) | ~$13/mo (Azure B1) |
| **Best for** | Documentation, sharing rules | Production automation |

### My Recommendation
- Start with **Option A** immediately (5 min)
- Add **Option B** when you need actual image processing in Copilot Studio
- Both can coexist — the Knowledge source explains the rules, the Tool executes them

---

## Quick Start: Option A in 5 Clicks

1. Open [Copilot Studio](https://copilotstudio.microsoft.com)
2. Select agent → **Knowledge** → **+ Add knowledge** → **Upload**
3. Download SKILL.md from https://github.com/David-X329/flowchart-to-excel-skill/blob/main/SKILL.md
4. Upload and save
5. Test: Ask "How do I extract System column from a flowchart?"

Done! Your Copilot agent now knows all the flowchart extraction rules.
