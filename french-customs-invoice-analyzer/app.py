import streamlit as st
import json
from modules.extractor import extract_text_from_pdf  # only for PDFs
from modules.vision_analyzer import analyze_invoice_image
from modules.web_search import search_text
from modules.eori_utils import find_eori_from_siren, find_eori_from_name_and_postal
from modules.airport_codes import get_airport_code
from modules.hs_resolver import get_hs_code_for_commodity

st.set_page_config(page_title="French Customs Invoice Analyzer", layout="wide")
st.title("📑 French Customs Invoice Analyzer")
st.markdown("Extracts EORI, customs value, HS codes, airport codes using AI vision + free web search.")

with st.sidebar:
    st.header("🔑 API Configuration")
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        groq_key = st.text_input("Groq API Key", type="password", 
                                 help="Required for vision analysis. Get from https://console.groq.com")
    use_web_search = st.checkbox("Enable Web Search", value=True)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload invoice (PDF/PNG/JPG)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file and groq_key:
    file_bytes = uploaded_file.read()
    file_type = uploaded_file.type
    
    with st.spinner("🔍 Analyzing invoice with AI vision..."):
        if file_type == "application/pdf":
            # For PDFs, we need to convert to images or use OCR; for now show message
            st.warning("PDF support coming soon. Please upload an image (PNG/JPG) for best results.")
            st.stop()
        else:
            invoice_data = analyze_invoice_image(file_bytes, groq_key)
    
    if "error" in invoice_data:
        st.error(f"Vision analysis failed: {invoice_data['error']}")
        if "raw_response" in invoice_data:
            st.text("Raw AI response:")
            st.code(invoice_data["raw_response"])
        st.stop()
    
    # Optional web search enrichment (same as before)
    if use_web_search:
        with st.spinner("🌐 Enriching with web search..."):
            # ... (same enrichment code as before, using invoice_data)
            pass
    
    # Display results
    st.subheader("📋 Extracted Customs Information")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sender Name", invoice_data.get("sender_name") or "❓")
        st.metric("Sender EORI", invoice_data.get("sender_eori") or "Not found")
        st.metric("Receiver Name", invoice_data.get("receiver_name") or "❓")
        st.metric("Receiver EORI", invoice_data.get("receiver_eori") or "Not found")
    with col2:
        st.metric("Document Number", invoice_data.get("document_number") or "❓")
        st.metric("Shipment Type", invoice_data.get("type_of_shipment") or "❓")
        st.metric("Airport Code", invoice_data.get("airport_code") or "Not found")
        value = invoice_data.get("value")
        st.metric("VAT-Free Value (€)", f"{value:,.2f}" if value else "Not found")
    
    st.subheader("📦 Commodities")
    if invoice_data.get("commodities"):
        st.dataframe(invoice_data["commodities"])
    else:
        st.info("No line items found.")
    
    st.download_button("💾 Download JSON Report",
                       data=json.dumps(invoice_data, indent=2, ensure_ascii=False),
                       file_name="customs_invoice_report.json",
                       mime="application/json")
else:
    st.info("👈 Upload an invoice image and enter your Groq API key.")
