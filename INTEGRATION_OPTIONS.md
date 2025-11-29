# Integration Options: Railway + Ollama GPU

## Current Setup

| Component | Location | URL |
|-----------|----------|-----|
| Streamlit Frontend | Railway (cloud) | https://pharmacie.up.railway.app |
| Ollama GPU Backend | Local GPU machine | http://localhost:8000 |

## The Problem

Railway is cloud-hosted and **cannot directly reach** your local GPU machine.

## Solutions

### Option 1: Local Network Only (Simplest)

Run the Ollama-enabled Streamlit locally on your pharmacy network:

```bash
cd C:\Users\sbcom\Development\claude-projects\pharmacy-ocr-railway

# Set Ollama backend URL (your GPU machine IP)
set OLLAMA_URL=http://192.168.1.100:8000

# Run Streamlit locally
streamlit run app_ollama.py
```

Access from any PC on network: `http://<this-pc-ip>:8501`

### Option 2: Ngrok Tunnel (Cloud + GPU)

Expose your local Ollama server to Railway:

```bash
# On GPU machine
ngrok http 8000
# Get URL like: https://abc123.ngrok.io
```

Then set Railway environment variable:
```
OLLAMA_URL=https://abc123.ngrok.io
```

Deploy `app_ollama.py` instead of `app.py` to Railway.

### Option 3: Dual Deployment

- **Railway** (https://pharmacie.up.railway.app) - Tesseract, for external/mobile use
- **Local Streamlit** (http://192.168.x.x:8501) - Ollama GPU, for pharmacy network

## Files

| File | Purpose |
|------|---------|
| `app.py` | Original Tesseract-only (Railway production) |
| `app_ollama.py` | Dual backend - Tesseract OR Ollama |
| `OLLAMA_GPU_BACKEND_GUIDE.md` | Full Ollama setup guide |

## Field Mapping

| Railway (Tesseract) | Ollama GPU | Notes |
|---------------------|------------|-------|
| date | date_originale | |
| prescriber | prescripteur | Includes CMQ license |
| medication | produit_prescrit | Full drug + strength + form |
| strength | (in produit_prescrit) | |
| form | (in produit_prescrit) | |
| quantity | qte_prescrite | |
| refills | nb_ren | |
| directions | posologie | Full instructions with duration |
| - | produit_emis | Dispensed product (may differ) |
| - | date_emission | Dispense date |

## Recommended Setup

For **pharmacy internal use**: Option 1 (local Streamlit + Ollama GPU)
- Fastest (local network)
- Best accuracy (vision model)
- No internet dependency

For **external/mobile access**: Keep Railway with Tesseract
- Always available
- Works from anywhere
- Good enough for simple prescriptions
