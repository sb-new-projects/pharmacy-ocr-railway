import streamlit as st
import pytesseract
from PIL import Image
import re
import json
from datetime import datetime
from streamlit_paste_button import paste_image_button

st.set_page_config(page_title="OCR Ordonnance Québec", page_icon="💊", layout="wide")

# Privacy notice
st.success("🔒 **GARANTIE DE CONFIDENTIALITÉ**: Aucune image ni donnée n'est sauvegardée. Tout est traité en mémoire et supprimé à la fermeture de cette page.")

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

# PASTE ZONE
st.markdown("### 📋 Coller depuis le presse-papiers")
st.info("**Processus en 3 secondes:** `Win+Maj+S` → Sélectionner l'ordonnance → Cliquer le bouton → `Ctrl+V`")

paste_result = paste_image_button(
    label="📋 Coller l'image",
    background_color="#00A0DC",
    hover_background_color="#0088C0",
    key="paste_prescription"
)

if paste_result.image_data is not None:
    image = paste_result.image_data

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📸 Ordonnance")
        st.image(image, use_column_width=True)

    with col2:
        st.subheader("📋 Champs extraits")

        with st.spinner("🔍 Lecture en cours..."):
            # OCR
            ocr_text = pytesseract.image_to_string(image, lang='eng+fra')

            # Extract
            fields = extract_prescription_only(ocr_text)

            st.markdown("### Prêt à copier-coller:")

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

            # Raw OCR display (always visible)
            st.markdown("### 🔍 Texte OCR brut:")
            st.text_area("", ocr_text, height=150, disabled=True)

            # Export
            st.markdown("### 💾 Exporter")
            json_data = json.dumps(fields, indent=2, ensure_ascii=False)

            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    "📥 Télécharger JSON",
                    json_data,
                    file_name=f"rx_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            with col_b:
                if st.button("📋 Copier tout"):
                    st.code(json_data, language='json')

else:
    st.markdown("""
    ### 🔒 Confidentialité et sécurité:
    - **AUCUNE BASE DE DONNÉES** - rien n'est sauvegardé
    - **AUCUN STOCKAGE** - images traitées en mémoire seulement
    - **AUCUN LOG** - les données d'ordonnance ne sont jamais enregistrées
    - **SUPPRESSION AUTO** - tout est effacé à la fermeture de la page
    - **CONFORME LPRPDE/Loi 25** - aucune rétention de données

    Chaque image est complètement isolée. Vos ordonnances ne touchent **jamais** un disque dur.

    ### ✅ Ce qui est extrait (de l'ordonnance):
    - **Date** - date de rédaction
    - **Prescripteur** - nom du Dr/Dre
    - **Médicament** - nom commercial ou générique
    - **Force** - dosage (10mg, 500mg, etc.)
    - **Forme** - caps, comp, crème, etc.
    - **Quantité** - nombre à servir
    - **Renouvellements** - nombre de répétitions
    - **Posologie** - instructions de prise

    ### ❌ Ce qui n'est PAS extrait:
    - **Info patient** (nom, DDN, tél, RAMQ) - déjà dans votre système
    - **DIN** - vous le cherchez selon le médicament
    - **Produit servi** - votre choix marque/générique
    - **Source** - votre fournisseur
    - **Format** - taille du paquet
    - **Date de service** - date du jour

    ### 🔄 Votre flux de travail:
    1. **Win+Maj+S** - Capture d'écran de l'ordonnance
    2. **Cliquer le bouton** - ci-dessus
    3. **Ctrl+V** - coller l'image
    4. **Copier les champs** - coller dans votre logiciel
    5. **Chercher le patient** - déjà dans le système
    6. **Chercher le DIN** - selon le médicament
    7. **Compléter la transaction**
    """)
