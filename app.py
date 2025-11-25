import streamlit as st
import pytesseract
from PIL import Image
import re
import json
from datetime import datetime
from streamlit_paste_button import paste_image_button

st.set_page_config(page_title="OCR Ordonnance Québec", page_icon="💊", layout="wide")

# RED WARNING - No patient identifiers
st.markdown("""
<div style="background-color: #FF4B4B; color: white; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 18px;">
⚠️ NE PAS CAPTURER: Nom du patient, date de naissance, téléphone, RAMQ ou tout identifiant personnel
</div>
""", unsafe_allow_html=True)

st.title("💊 OCR Ordonnance Québec")

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

# PASTE ZONE - Simple instruction
st.markdown("##### 1️⃣ `Win+Maj+S` pour capturer l'ordonnance &nbsp;&nbsp; 2️⃣ Appuyez sur le bouton ci-dessous")

paste_result = paste_image_button(
    label="📋 APPUYEZ ICI POUR COLLER LA CAPTURE",
    background_color="#00A0DC",
    hover_background_color="#0088C0",
    key="paste_prescription"
)

if paste_result.image_data is not None:
    image = paste_result.image_data

    with st.spinner("🔍 Lecture en cours..."):
        # OCR
        ocr_text = pytesseract.image_to_string(image, lang='eng+fra')
        # Extract
        fields = extract_prescription_only(ocr_text)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📸 Ordonnance")
        st.image(image, use_container_width=True)

    with col2:
        # Tabs for switching between extracted fields and raw OCR
        tab1, tab2 = st.tabs(["📋 Champs extraits", "🔍 Texte OCR brut"])

        with tab1:
            st.markdown("### Prêt à copier-coller:")

            # Date
            if fields['date']:
                st.code(f"📅 Date: {fields['date']}")

            # Prescriber
            if fields['prescriber']:
                st.code(f"👨‍⚕️ Prescripteur: {fields['prescriber']}")

            # Medication
            if fields['medication']:
                st.code(f"💊 Médicament: {fields['medication']}")

            # Strength
            if fields['strength']:
                st.code(f"⚖️ Force: {fields['strength']}")

            # Form
            if fields['form']:
                st.code(f"📦 Forme: {fields['form']}")

            # Quantity
            if fields['quantity']:
                st.code(f"🔢 Quantité: {fields['quantity']}")

            # Refills
            if fields['refills']:
                st.code(f"🔄 Renouvellements: {fields['refills']}")

            # Directions
            if fields['directions']:
                st.code(f"📝 Posologie: {fields['directions']}")

            # Export
            st.markdown("---")
            json_data = json.dumps(fields, indent=2, ensure_ascii=False)
            st.download_button(
                "📥 Télécharger JSON",
                json_data,
                file_name=f"rx_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

        with tab2:
            st.markdown("### Texte complet extrait par OCR:")
            st.text_area("", ocr_text, height=400, disabled=True, label_visibility="collapsed")

else:
    st.markdown("""
    ### ✅ Ce qui est extrait:
    Date, Prescripteur, Médicament, Force, Forme, Quantité, Renouvellements, Posologie

    ### 🔄 Comment utiliser:
    1. **Win+Maj+S** → Capturer la section ordonnance (sans info patient!)
    2. **Appuyer sur le bouton bleu** ci-dessus
    3. **Copier les champs** → Coller dans votre logiciel

    ---
    🔒 *Aucune donnée sauvegardée. Tout est supprimé à la fermeture.*
    """)
