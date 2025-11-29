"""
Quebec Pharmacy OCR - Dual Backend Version
Supports: Tesseract (Railway cloud) OR Ollama GPU (local network)

Set OLLAMA_URL environment variable to use Ollama backend:
  export OLLAMA_URL=http://192.168.1.100:8000

Without OLLAMA_URL, falls back to Tesseract.
"""
import streamlit as st
import pytesseract
from PIL import Image
import re
import json
import base64
import os
from datetime import datetime
from streamlit_paste_button import paste_image_button

# Check for Ollama backend
OLLAMA_URL = os.environ.get('OLLAMA_URL', '')
USE_OLLAMA = bool(OLLAMA_URL)

if USE_OLLAMA:
    import httpx

st.set_page_config(page_title="OCR Ordonnance Québec", page_icon="💊", layout="wide")

# RED WARNING - No patient identifiers
st.markdown("""
<div style="background-color: #FF4B4B; color: white; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 18px;">
⚠️ NE PAS CAPTURER: Nom du patient, date de naissance, téléphone, RAMQ ou tout identifiant personnel
</div>
""", unsafe_allow_html=True)

st.title("💊 OCR Ordonnance Québec")

# Show backend status
if USE_OLLAMA:
    st.success(f"🚀 Backend GPU Ollama: {OLLAMA_URL}")
else:
    st.info("🔤 Backend Tesseract (cloud)")


def extract_with_ollama(image):
    """Send image to Ollama GPU backend"""
    # Convert PIL image to base64
    import io
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_b64 = base64.b64encode(buffer.getvalue()).decode()

    try:
        response = httpx.post(
            f"{OLLAMA_URL}/extract",
            json={'image': img_b64},
            timeout=120
        )
        data = response.json()

        # Map Ollama fields to our format
        fields = {
            'date': data.get('date_originale', ''),
            'prescriber': data.get('prescripteur', ''),
            'medication': data.get('produit_prescrit', ''),
            'strength': '',  # Included in produit_prescrit
            'form': '',  # Included in produit_prescrit
            'quantity': data.get('qte_prescrite', ''),
            'refills': data.get('nb_ren', ''),
            'directions': data.get('posologie', ''),
        }

        # Extra fields from Ollama
        extra = {
            'produit_emis': data.get('produit_emis', ''),
            'date_emission': data.get('date_emission', ''),
        }

        raw_text = data.get('raw_text', str(data))
        return fields, extra, raw_text

    except Exception as e:
        st.error(f"Erreur Ollama: {e}")
        return None, None, str(e)


def extract_with_tesseract(image):
    """Use local Tesseract OCR"""
    ocr_text = pytesseract.image_to_string(image, lang='eng+fra')

    fields = {}

    # Date patterns
    date_patterns = [
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',
        r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',
    ]
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, ocr_text))

    # Prescriber
    prescriber_patterns = [
        r'(?:Dr\.?|Dre\.?)\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
        r'MD[:\s]*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
    ]
    prescribers = []
    for pattern in prescriber_patterns:
        prescribers.extend(re.findall(pattern, ocr_text))

    # Medication
    med_pattern = r'\b([A-Z][a-z]*[-]?[A-Z]?[a-z]+(?:ine|ol|ide|cin|mine|pam|tan|lin|xin|done|pril|stat|one|pine|mab|nib|fungin)?)\b'
    medications = re.findall(med_pattern, ocr_text)
    stop_words = {'Dr', 'Dre', 'Patient', 'Date', 'Rx', 'Sig', 'Qty', 'Refills', 'Name', 'Phone', 'Address', 'RAMQ'}
    medications = [m for m in medications if m not in stop_words and len(m) > 3]

    # Strength
    strength_pattern = r'(\d+(?:\.\d+)?\s*(?:mg|MG|ml|ML|mcg|MCG|g|G|units?|UNITS?)(?:/\d+(?:mg|ml))?)'
    strengths = re.findall(strength_pattern, ocr_text)

    # Form
    form_pattern = r'\b(cap|caps|capsule|capsules|tab|tabs|tablet|tablets|comp|comprimé|comprimés|cream|crème|ointment|syrup|sirop|solution|suspension|injection|inhalation)\b'
    forms = re.findall(form_pattern, ocr_text, re.IGNORECASE)

    # Quantity
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

    # Refills
    refill_patterns = [
        r'Refills?[:\s]*(\d+)',
        r'Ren(?:ouvellements?)?[:\s]*(\d+)',
        r'Rép[ée]t[ée]?[:\s]*(\d+)',
        r'Rep[:\s]*(\d+)',
    ]
    refills = []
    for pattern in refill_patterns:
        refills.extend(re.findall(pattern, ocr_text, re.IGNORECASE))

    # Directions
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

    fields['date'] = dates[0] if dates else ""
    fields['prescriber'] = prescribers[0].strip() if prescribers else ""
    fields['medication'] = medications[0] if medications else ""
    fields['strength'] = strengths[0] if strengths else ""
    fields['form'] = forms[0] if forms else ""
    fields['quantity'] = quantities[0] if quantities else ""
    fields['refills'] = refills[0] if refills else ""
    fields['directions'] = directions[0].strip() if directions else ""

    return fields, {}, ocr_text


# PASTE ZONE
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
        if USE_OLLAMA:
            fields, extra, raw_text = extract_with_ollama(image)
        else:
            fields, extra, raw_text = extract_with_tesseract(image)

    if fields:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📸 Ordonnance")
            st.image(image, use_column_width=True)

        with col2:
            tab1, tab2 = st.tabs(["📋 Champs extraits", "🔍 Texte OCR brut"])

            with tab1:
                st.markdown("### Prêt à copier-coller:")

                if fields.get('date'):
                    st.code(f"📅 Date: {fields['date']}")
                if fields.get('prescriber'):
                    st.code(f"👨‍⚕️ Prescripteur: {fields['prescriber']}")
                if fields.get('medication'):
                    st.code(f"💊 Médicament: {fields['medication']}")
                if fields.get('strength'):
                    st.code(f"⚖️ Force: {fields['strength']}")
                if fields.get('form'):
                    st.code(f"📦 Forme: {fields['form']}")
                if fields.get('quantity'):
                    st.code(f"🔢 Quantité: {fields['quantity']}")
                if fields.get('refills'):
                    st.code(f"🔄 Renouvellements: {fields['refills']}")
                if fields.get('directions'):
                    st.code(f"📝 Posologie: {fields['directions']}")

                # Extra Ollama fields
                if extra:
                    st.markdown("---")
                    st.markdown("### Champs supplémentaires (Ollama):")
                    if extra.get('produit_emis'):
                        st.code(f"💉 Produit émis: {extra['produit_emis']}")
                    if extra.get('date_emission'):
                        st.code(f"📆 Date émission: {extra['date_emission']}")

                st.markdown("---")
                json_data = json.dumps(fields, indent=2, ensure_ascii=False)
                st.download_button(
                    "📥 Télécharger JSON",
                    json_data,
                    file_name=f"rx_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

            with tab2:
                st.markdown("### Texte complet extrait:")
                st.text_area("", raw_text, height=400, disabled=True, label_visibility="collapsed")

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
