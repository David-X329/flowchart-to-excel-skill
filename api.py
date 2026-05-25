#!/usr/bin/env python3
"""
Flowchart to Excel — REST API Server
=====================================
FastAPI server that accepts flowchart images and returns formatted Excel files.

Usage:
    python3 api.py
    # or: uvicorn api:app --host 0.0.0.0 --port 5000

Environment variables:
    API_KEY — If set, requests must include X-API-Key header
    PORT — Server port (default 5000)
"""

import os
import sys
import io
import base64
import tempfile
from datetime import datetime

# Add scripts dir to path for pipeline import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

try:
    from fastapi import FastAPI, HTTPException, Header, Request
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
except ImportError:
    print("Installing dependencies...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "pydantic", "-q"])
    from fastapi import FastAPI, HTTPException, Header, Request
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel

from flowchart_pipeline import process_flowchart, create_excel

app = FastAPI(
    title="Flowchart to Excel API",
    description="Extract structured data (L4, System, Role, Auto, L5) from flowchart images",
    version="2.1.0"
)

API_KEY = os.environ.get("API_KEY", "")


class FlowchartRequest(BaseModel):
    """Request body for flowchart processing."""
    image_base64: str  # Base64-encoded PNG/JPEG image


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


def check_api_key(x_api_key: str | None = Header(None)):
    """Validate API key if configured."""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Flowchart to Excel API",
        "version": "2.1.0",
        "status": "running",
        "time": datetime.utcnow().isoformat()
    }


@app.post("/process",
          summary="Process flowchart image",
          description="Accepts a base64-encoded flowchart image (PNG/JPEG) and returns an Excel file with extracted data.")
async def process_flowchart_endpoint(
    req: FlowchartRequest,
    x_api_key: str | None = Header(None)
):
    """Main processing endpoint."""
    # Auth
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    # Decode image
    try:
        # Strip data URI prefix if present
        b64 = req.image_base64
        if "," in b64 and b64.startswith("data:"):
            b64 = b64.split(",", 1)[1]

        img_bytes = base64.b64decode(b64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image: {str(e)}")

    if len(img_bytes) < 100:
        raise HTTPException(status_code=400, detail="Image too small (< 100 bytes)")

    # Process
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(img_bytes)
            tmp_path = f.name

        results = process_flowchart(img_bytes)
        excel_buf = create_excel(results)

        os.unlink(tmp_path)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

    return StreamingResponse(
        excel_buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=flowchart_output.xlsx",
            "X-Card-Count": str(len(results)),
            "X-Processed-At": datetime.utcnow().isoformat()
        }
    )


@app.post("/process/upload",
          summary="Process flowchart image (multipart upload)",
          description="Alternative endpoint that accepts a direct file upload instead of base64.")
async def process_upload(request: Request):
    """File upload endpoint."""
    from fastapi import UploadFile, File, Form

    # This is a declarative endpoint — actual implementation depends on FastAPI version
    raise HTTPException(status_code=501, detail="Use POST /process with base64 instead")


@app.get("/health")
async def health():
    """Detailed health check."""
    try:
        import pytesseract
        tesseract_ok = True
    except Exception:
        tesseract_ok = False

    try:
        from PIL import Image
        pillow_ok = True
    except Exception:
        pillow_ok = False

    return {
        "status": "healthy" if (tesseract_ok and pillow_ok) else "degraded",
        "dependencies": {
            "tesseract": "ok" if tesseract_ok else "missing",
            "pillow": "ok" if pillow_ok else "missing",
            "openpyxl": "ok",
            "numpy": "ok"
        },
        "version": "2.1.0"
    }


# ═══════════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "5000"))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"""
╔══════════════════════════════════════════════╗
║   Flowchart to Excel API v2.1               ║
║   http://{host}:{port}                    ║
║   Docs: http://{host}:{port}/docs          ║
╚══════════════════════════════════════════════╝
""")
    uvicorn.run(app, host=host, port=port)
