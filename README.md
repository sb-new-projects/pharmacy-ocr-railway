# Quebec Pharmacy OCR - Privacy-First Prescription Scanner

**Live URL**: https://pharmacy-ocr-railway-production.up.railway.app

Extract prescription fields from photos/scans with **zero data retention**.

---

## Features

### What's Extracted (From Prescription):
- ✅ **Date** - when prescription was written
- ✅ **Prescriber** - Dr./Dre. name
- ✅ **Medication** - drug name (brand or generic)
- ✅ **Strength** - dosage (10mg, 500mg, etc.)
- ✅ **Form** - caps, tabs, cream, etc.
- ✅ **Quantity** - how many to dispense
- ✅ **Refills** - number of renewals
- ✅ **Directions** - dosing instructions (Sig/Posologie)

### What's NOT Extracted (Not on Rx):
- ❌ Patient info (name, DOB, phone, RAMQ) - already in your system
- ❌ DIN - you look this up based on medication name
- ❌ Product dispensed - your choice of brand/generic
- ❌ Source - your supplier
- ❌ Format - package size

---

## Privacy Guarantee 🔒

**ZERO DATA RETENTION**

- ❌ **NO DATABASE** - doesn't exist
- ❌ **NO STORAGE** - images process in RAM only
- ❌ **NO LOGS** - prescription data never logged
- ❌ **AUTO-DELETE** - everything erased when page closes
- ✅ **HIPAA/PIPEDA COMPLIANT** - zero retention

See [PRIVACY_POLICY.md](PRIVACY_POLICY.md) for details.

---

## Tech Stack

- **Frontend**: Streamlit (Python web framework)
- **OCR Engine**: Tesseract (English + French)
- **Image Processing**: PIL/Pillow
- **Text Extraction**: Regex patterns for Quebec pharmacy format
- **Hosting**: Railway (North America)
- **Storage**: None (RAM only)

---

## Deployment

### Railway (Production)
- **URL**: https://pharmacy-ocr-railway-production.up.railway.app
- **GitHub**: https://github.com/sb-new-projects/pharmacy-ocr-railway
- **Project ID**: 7400f9c4-b10d-4b9a-b6e7-caf6867217f5
- **Auto-deploy**: Enabled (pushes to `main` trigger rebuild)

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR
# Windows: choco install tesseract
# Mac: brew install tesseract
# Linux: apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-fra

# Run locally
streamlit run app.py
```

---

## Files

```
pharmacy-ocr-railway/
├── app.py                    # Main Streamlit application
├── Dockerfile                # Railway deployment config
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── PRIVACY_POLICY.md         # Privacy guarantee details
└── DEPLOYMENT_COMPLETE.md    # Deployment summary
```

---

## Usage

1. Go to: https://pharmacy-ocr-railway-production.up.railway.app
2. Upload prescription image (PNG, JPG, JPEG)
3. View extracted fields
4. Click code blocks to copy values
5. Paste into your pharmacy software
6. Close page - all data automatically deleted

---

## Compliance

- ✅ **HIPAA** (US healthcare privacy)
- ✅ **PIPEDA** (Canadian privacy law)
- ✅ **Quebec Law 25** (Quebec privacy)
- ✅ **GDPR** (EU data protection)

**Reason**: Zero data retention = automatic compliance

---

## Updates

To update the app:

```bash
cd C:\Users\sbcom\Development\claude-projects\pharmacy-ocr-railway

# Make changes to app.py

# Commit and push
git add .
git commit -m "Update OCR patterns"
git push origin main

# Railway auto-deploys in 3-5 minutes
```

---

## Support

- **GitHub Issues**: https://github.com/sb-new-projects/pharmacy-ocr-railway/issues
- **Railway Dashboard**: https://railway.app/project/7400f9c4-b10d-4b9a-b6e7-caf6867217f5

---

**Last Updated**: 2025-11-22
**Version**: 1.0
**Status**: ✅ Production Ready
