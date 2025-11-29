# Quebec Pharmacy OCR - Simple Ollama Setup Guide

## Context: The Full System

### Production Frontend (Railway)
- **URL**: https://pharmacie.up.railway.app
- **Stack**: Streamlit + Tesseract OCR
- **Method**: Regex-based text extraction
- **Limitation**: Tesseract struggles with pharmacy label layouts

### Local GPU Backend (This Project)
- **Goal**: Replace Tesseract with Ollama vision model
- **Hardware**: NVIDIA RTX 5070 Ti (12GB VRAM)
- **Advantage**: Vision model understands document structure, not just text

---

## The Problem

The original GPU setup used PyTorch + HuggingFace Transformers to load vision models directly:

```python
# OLD APPROACH - caused crashes
from transformers import Qwen2VLForConditionalGeneration
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "JackChew/Qwen2-VL-2B-OCR",
    device_map="cuda"
)
```

This caused:
- Frequent GPU crashes on Windows
- Complex dependency issues (bitsandbytes doesn't work well on Windows)
- Memory management problems
- Unreliable operation

## The Solution

**Use Ollama instead.** Ollama handles all GPU/model management internally - no PyTorch needed in our code.

### Architecture

```
[Your App] --> [simple_server.py] --> [Ollama API] --> [GPU]
                  (FastAPI)           (localhost:11434)
```

- `simple_server.py` is ~150 lines of Python
- Only dependencies: `fastapi`, `uvicorn`, `httpx`, `pillow`
- No PyTorch, no transformers, no GPU code
- Ollama handles all the GPU stuff

---

## Setup

### 1. Install Ollama

Download from: https://ollama.ai

### 2. Pull a Vision Model

```bash
ollama pull qwen2.5vl:3b
```

Other options:
- `llava:7b` - larger, more accurate
- `llava:13b` - even better accuracy
- `moondream:latest` - smallest, fastest

### 3. Start Ollama

```bash
ollama serve
```

Runs on `http://localhost:11434`

### 4. Run the OCR Server

```bash
.\run_simple.bat
```

Or manually:
```bash
venv311\Scripts\python.exe simple_server.py
```

Server runs on `http://localhost:8000`

---

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Status
```bash
curl http://localhost:8000/status
```

### Extract Prescription Fields
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"image": "<base64-encoded-image>"}'
```

### Python Example
```python
import base64
import httpx

# Read image
with open('prescription.png', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

# Call API
response = httpx.post(
    'http://localhost:8000/extract',
    json={'image': img_b64},
    timeout=120
)

print(response.json())
```

---

## Extraction Approach

### Verbatim Extraction

The prompt tells the model to copy text EXACTLY as printed - no interpretation:

```
Read this Quebec pharmacy prescription label and extract the text EXACTLY as written.
DO NOT interpret or summarize. Copy the text VERBATIM.
```

This ensures:
- Full posologie with durations: `1 co DIE PO 84j` (not just `1 co DIE PO`)
- Quantities as written: `15 jour(s)`, `#10`, `30j`
- Refills as shown: `R12`, `R4`, `NR`

### Fields Extracted

| Field | Description | Example |
|-------|-------------|---------|
| date_originale | Original Rx date | 2025-01-16 |
| prescripteur | Doctor + license | Dr NAME (CMQ: 12345) |
| produit_prescrit | Prescribed drug | LAMISIL 250MG (COMPRIME) |
| produit_emis | Dispensed drug | LAMISIL 250MG (COMPRIME) |
| date_emission | Fill date | 2025-07-29 |
| qte_prescrite | Quantity/duration | 84j, 15 jour(s), #10 |
| nb_ren | Refills | 12, 4, 0 |
| posologie | Full dosing instructions | 1 co DIE PO 84j |

---

## Testing

Test images are in `tests/rx-samples-to-test/`:
- rx1.png through rx7.png

Run all tests:
```python
import base64
import httpx
import os

test_dir = 'tests/rx-samples-to-test'
for f in sorted(os.listdir(test_dir)):
    if f.endswith('.png'):
        with open(os.path.join(test_dir, f), 'rb') as img:
            img_b64 = base64.b64encode(img.read()).decode()

        r = httpx.post('http://localhost:8000/extract',
                       json={'image': img_b64}, timeout=120)
        print(f"{f}: {r.json().get('posologie')}")
```

---

## Troubleshooting

### Ollama not running
```
Error: Ollama not available
```
Fix: Start Ollama with `ollama serve`

### Model not found
```
Error: Model qwen2.5vl:3b not found
```
Fix: `ollama pull qwen2.5vl:3b`

### Port already in use
```
Error: [Errno 10048] port 8000 in use
```
Fix: Kill existing process:
```bash
netstat -ano | grep :8000
taskkill /F /PID <pid>
```

### Slow first request
Normal - model loads into GPU on first request. Subsequent requests are fast.

---

## Files

| File | Purpose |
|------|---------|
| `simple_server.py` | Main server (Ollama-only) |
| `run_simple.bat` | Start script |
| `GUIDE.md` | This guide |
| `CLAUDE.md` | Project instructions |

### Old Files (not recommended)
| File | Issue |
|------|-------|
| `run.bat` | Uses complex server |
| `src/server.py` | PyTorch dependencies, crashes |
| `src/ocr_engine.py` | Complex multi-backend, unstable |
| `efs/src/vlm_ocr_server.py` | Direct GPU loading, crashes |

---

## Why This Works

1. **Ollama manages GPU** - handles VRAM, model loading/unloading, CUDA
2. **Simple HTTP API** - we just send images, get JSON back
3. **No PyTorch in our code** - no dependency conflicts
4. **Verbatim prompt** - model reads exactly what's printed
5. **Single responsibility** - server only does HTTP, Ollama does AI

---

## Field Mapping: Railway vs Local

| Railway Streamlit (Tesseract) | Local Ollama Server | Notes |
|-------------------------------|---------------------|-------|
| date | date_originale | Original Rx date |
| prescriber | prescripteur | Doctor + CMQ license |
| medication | produit_prescrit | Prescribed drug |
| (not extracted) | produit_emis | Dispensed drug (may differ) |
| (not extracted) | date_emission | Fill/dispense date |
| strength + form | (in produit_prescrit) | Combined in drug name |
| quantity | qte_prescrite | Quantity/duration |
| refills | nb_ren | Number of refills |
| directions | posologie | Dosing instructions |

The local Ollama server uses **Quebec RxPro pharmacy system field names** which are more specific to the actual labels.

---

## Handoff Reference

Original handoff package from `handoff_gpu_ocr.zip`:
- `app.py` - Streamlit frontend (Railway production)
- `GRADIO_BACKEND_SPECS.md` - Specs for Gradio alternative
- `Dockerfile` - Container config with Tesseract

The handoff goal was to build a Gradio app, but we went with **FastAPI + Ollama** instead because:
1. Simpler to integrate with existing systems
2. REST API is more flexible than Gradio interface
3. Same endpoints work for web, mobile, or batch processing

---

## Next Steps (Optional)

1. **Build Gradio UI** - If you want a web interface like Railway
2. **Try larger model** - `llava:7b` or `qwen2.5vl:7b` for better accuracy
3. **Connect to Railway** - Railway frontend could call this local API instead of Tesseract
