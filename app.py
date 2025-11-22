import streamlit as st
import pytesseract
from PIL import Image
import re

st.set_page_config(page_title="Quebec Pharmacy OCR", page_icon="💊", layout="wide")
st.title("💊 Quebec Pharmacy OCR")

uploaded_file = st.file_uploader("Upload Prescription Image", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    col1, col2 = st.columns([1, 1])
    with col1:
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)
    with col2:
        with st.spinner("Extracting..."):
            text = pytesseract.image_to_string(image, lang='eng+fra')
            patterns = {
                'Medication': r'(?:rx|med)[\s:]*([a-z]+(?:ine|ol|cillin))',
                'Strength': r'(\d+(?:\.\d+)?\s*(?:mg|ml))',
                'Quantity': r'(?:qty|#)[\s:]*(\d+)',
                'Directions': r'(?:sig)[\s:]*([^\n]{10,100})',
                'Refills': r'(?:refills?)[\s:]*(\d+)'
            }
            for name, pattern in patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                value = match.group(1) if match else "Not found"
                st.text_input(name, value, disabled=True)
                st.code(value)
else:
    st.info("Upload a prescription image to begin")
