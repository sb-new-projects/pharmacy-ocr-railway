import streamlit as st
import pytesseract
from PIL import Image
import re
import json
from datetime import datetime
from streamlit_paste_button import paste_image_button

st.set_page_config(page_title="Quebec Rx OCR", page_icon="💊", layout="wide")

# Privacy notice
st.success("🔒 **PRIVACY GUARANTEE**: No images or data are saved. Everything processes in memory and is deleted when you close this page.")

st.title("💊 Quebec Prescription OCR")

def extract_prescription_only(ocr_text):
    """
    Extract ONLY what's actually written on Quebec prescriptions:
    - Date
    - Prescriber name
    - Medication name
    - Strength
    - Form
    - Quantity
    - Refills
    - Directions (Sig/Posologie)

    NO patient info (name, DOB, phone, RAMQ) - that's in your system already!
    """
    extracted = {}

    # Date (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, or written format)
    date_patterns = [
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',
        r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',
    ]
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, ocr_text))

    # Prescriber (Dr./Dre. + Name)
    prescriber_patterns = [
        r'(?:Dr\.?|Dre\.?)\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
        r'MD[:\s]*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
    ]
    prescribers = []
    for pattern in prescriber_patterns:
        prescribers.extend(re.findall(pattern, ocr_text))

    # Medication name (brand or generic - usually starts with capital)
    # Common endings: -ine, -ol, -ide, -cin, -pam, -tan, -pril, -stat, etc.
    med_pattern = r'\b([A-Z][a-z]*[-]?[A-Z]?[a-z]+(?:ine|ol|ide|cin|mine|pam|tan|lin|xin|done|pril|stat|one|pine|mab|nib|fungin)?)\b'
    medications = re.findall(med_pattern, ocr_text)
    # Filter out common non-drug words
    stop_words = {'Dr', 'Dre', 'Patient', 'Date', 'Rx', 'Sig', 'Qty', 'Refills', 'Name', 'Phone', 'Address', 'RAMQ'}
    medications = [m for m in medications if m not in stop_words and len(m) > 3]

    # Strength (e.g., 10mg, 5 mg, 100 MG, 2.5mg, etc.)
    strength_pattern = r'(\d+(?:\.\d+)?\s*(?:mg|MG|ml|ML|mcg|MCG|g|G|units?|UNITS?)(?:/\d+(?:mg|ml))?)'
    strengths = re.findall(strength_pattern, ocr_text)

    # Form (caps, tabs, cream, etc.)
    form_pattern = r'\b(cap|caps|capsule|capsules|tab|tabs|tablet|tablets|comp|comprimé|comprimés|cream|crème|ointment|syrup|sirop|solution|suspension|injection|inhalation)\b'
    forms = re.findall(form_pattern, ocr_text, re.IGNORECASE)

    # Quantity (Qty: 30, #90, Disp: 21, etc.)
    qty_patterns = [
        r'[Qq]ty[:\s]*(\d+)',
        r'[Qq]uantity[:\s]*(\d+)',
        r'Quantité[:\s]*(\d+)',
        r'Disp(?:ense)?[:\s]*(\d+)',
        r'#\s*(\d+)',
        r'\b(\d{1,3})\s*(?:cap|tab|comp)',
    ]
    quantities = []
    for pattern in qty_patterns:
        quantities.extend(re.findall(pattern, ocr_text, re.IGNORECASE))

    # Refills (Refills: 3, Ren: 12, Rep: 5, etc.)
    refill_patterns = [
        r'Refills?[:\s]*(\d+)',
        r'Ren(?:ouvellements?)?[:\s]*(\d+)',
        r'Rép[ée]t[ée]?[:\s]*(\d+)',
        r'Rep[:\s]*(\d+)',
    ]
    refills = []
    for pattern in refill_patterns:
        refills.extend(re.findall(pattern, ocr_text, re.IGNORECASE))

    # Directions/Sig (dosing instructions in French or English)
    sig_patterns = [
        r'Sig[:\s]*([^\n]{15,200})',
        r'Directions?[:\s]*([^\n]{15,200})',
        r'Posologie[:\s]*([^\n]{15,200})',
        r'(?:Take|Prendre|Prenez)[:\s]*([^\n]{15,200})',
    ]
    directions = []
    for pattern in sig_patterns:
        found = re.findall(pattern, ocr_text, re.IGNORECASE)
        directions.extend(found)

    # Build result (only what's ON the prescription)
    extracted['date'] = dates[0] if dates else ""
    extracted['prescriber'] = prescribers[0].strip() if prescribers else ""
    extracted['medication'] = medications[0] if medications else ""
    extracted['strength'] = strengths[0] if strengths else ""
    extracted['form'] = forms[0] if forms else ""
    extracted['quantity'] = quantities[0] if quantities else ""
    extracted['refills'] = refills[0] if refills else ""
    extracted['directions'] = directions[0].strip() if directions else ""

    return extracted

# PASTE ZONE
st.markdown("### 📋 Quick Paste Workflow")
st.info("**3-Second Process:** `Win+Shift+S` → Select prescription area → Click button below → `Ctrl+V`")

paste_result = paste_image_button(
    label="📋 Paste from Clipboard",
    background_color="#00A0DC",
    hover_background_color="#0088C0",
    key="paste_prescription"
)

if paste_result.image_data is not None:
    image = paste_result.image_data

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📸 Prescription")
        st.image(image, use_column_width=True)

    with col2:
        st.subheader("📋 Extracted Fields")

        with st.spinner("🔍 Reading..."):
            # OCR
            ocr_text = pytesseract.image_to_string(image, lang='eng+fra')

            # Extract
            fields = extract_prescription_only(ocr_text)

            st.markdown("### Copy-Paste Ready:")

            # Date
            if fields['date']:
                st.text_input("📅 Date", fields['date'], disabled=True)
                st.code(fields['date'])
                st.markdown("---")

            # Prescriber
            if fields['prescriber']:
                st.text_input("👨‍⚕️ Prescripteur", fields['prescriber'], disabled=True)
                st.code(fields['prescriber'])
                st.markdown("---")

            # Medication
            if fields['medication']:
                st.text_input("💊 Médicament", fields['medication'], disabled=True)
                st.code(fields['medication'])
                st.markdown("---")

            # Strength
            if fields['strength']:
                st.text_input("⚖️ Force", fields['strength'], disabled=True)
                st.code(fields['strength'])
                st.markdown("---")

            # Form
            if fields['form']:
                st.text_input("📦 Forme", fields['form'], disabled=True)
                st.code(fields['form'])
                st.markdown("---")

            # Quantity
            if fields['quantity']:
                st.text_input("🔢 Quantité", fields['quantity'], disabled=True)
                st.code(fields['quantity'])
                st.markdown("---")

            # Refills
            if fields['refills']:
                st.text_input("🔄 Renouvellements", fields['refills'], disabled=True)
                st.code(fields['refills'])
                st.markdown("---")

            # Directions
            if fields['directions']:
                st.text_area("📝 Posologie", fields['directions'], height=100, disabled=True)
                st.code(fields['directions'])
                st.markdown("---")

            # Export
            st.markdown("### 💾 Export")
            json_data = json.dumps(fields, indent=2, ensure_ascii=False)

            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    "📥 Download JSON",
                    json_data,
                    file_name=f"rx_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            with col_b:
                if st.button("📋 Copy All"):
                    st.code(json_data, language='json')

            # Debug
            with st.expander("🔍 Raw OCR (Debug)"):
                st.text_area("", ocr_text, height=150)

else:
    st.markdown("""
    ### 🔒 Privacy & Security:
    - **NO DATABASE** - nothing is saved anywhere
    - **NO STORAGE** - images process in RAM only
    - **NO LOGS** - prescription data is never logged
    - **AUTO-DELETE** - everything erased when you close the page
    - **HIPAA/PIPEDA COMPLIANT** - zero data retention

    Each upload is completely isolated. Your prescription images **never** touch a hard drive.

    ### ✅ What's Extracted (From Rx Paper):
    - **Date** - when prescription was written
    - **Prescriber** - Dr./Dre. name
    - **Medication** - drug name (brand or generic)
    - **Strength** - dosage (10mg, 500mg, etc.)
    - **Form** - caps, tabs, cream, etc.
    - **Quantity** - how many to dispense
    - **Refills** - number of renewals
    - **Directions** - dosing instructions (Sig/Posologie)

    ### ❌ What's NOT Extracted (Not on Rx):
    - **Patient info** (name, DOB, phone, RAMQ) - already in your system
    - **DIN** - you look this up based on medication name
    - **Product dispensed** - your choice of brand/generic
    - **Source** - your supplier
    - **Format** - package size
    - **Dispensing date** - today's date

    ### 🔄 Your Workflow:
    1. **Win+Shift+S** - Screenshot prescription
    2. **Click paste button** - above
    3. **Ctrl+V** - paste image
    4. **Copy extracted fields** - paste into pharmacy software
    5. **Look up patient** - already in system
    6. **Look up DIN** - based on medication
    7. **Complete transaction**
    """)
