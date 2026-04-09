import streamlit as st
import json
import re
from modules.extractor import extract_text_from_pdf, extract_text_from_image
from modules.llm_analyzer import analyze_invoice
from modules.web_search import search_text
from modules.eori_utils import find_eori_from_siren, find_eori_from_name_and_postal
from modules.airport_codes import get_airport_code
from modules.hs_resolver import get_hs_code_for_commodity

st.set_page_config(page_title="French Customs Invoice Analyzer", layout="wide")
st.title("📑 French Customs Invoice Analyzer")
st.markdown("Extracts EORI, customs value, HS codes, airport codes, and more using AI + free web search.")

with st.sidebar:
    st.header("🔑 API Configuration")
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        groq_key = st.text_input("Groq API Key", type="password", help="Optional for regex mode, but keep for web search")
    use_web_search = st.checkbox("Enable Web Search", value=True)
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload invoice (PDF/PNG/JPG)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    with st.spinner("📄 Extracting text..."):
        file_bytes = uploaded_file.read()
        if uploaded_file.type == "application/pdf":
            raw_text = extract_text_from_pdf(file_bytes)
        else:
            raw_text = extract_text_from_image(file_bytes)

    if raw_text.startswith("Error"):
        st.error(raw_text)
        st.stop()

    st.success("✅ Text extraction complete.")

    with st.spinner("🔍 Analyzing with regex patterns..."):
        invoice_data = analyze_invoice(raw_text, groq_key)  # groq_key not used in regex version

    if use_web_search:
        with st.spinner("🌐 Enriching with web search..."):
            shipment_type = invoice_data.get("type_of_shipment", "")
            if shipment_type != "C2C":
                if not invoice_data.get("sender_eori") and invoice_data.get("sender_siren"):
                    eori = find_eori_from_siren(invoice_data["sender_siren"])
                    if eori:
                        invoice_data["sender_eori"] = eori
                if not invoice_data.get("sender_eori") and invoice_data.get("sender_name"):
                    postal_match = re.search(r'\b(\d{5})\b', raw_text)
                    postal_code = postal_match.group(1) if postal_match else None
                    if postal_code:
                        eori = find_eori_from_name_and_postal(invoice_data["sender_name"], postal_code)
                        if eori:
                            invoice_data["sender_eori"] = eori
            else:
                invoice_data["sender_eori"] = None

            if invoice_data.get("receiver_country"):
                airport_code = get_airport_code(invoice_data["receiver_country"])
                if airport_code:
                    invoice_data["airport_code"] = airport_code

            for idx, item in enumerate(invoice_data.get("commodities", [])):
                if not item.get("hs_code") and (item.get("common_name_en") or item.get("description_original")):
                    hs = get_hs_code_for_commodity(item)
                    if hs:
                        invoice_data["commodities"][idx]["hs_code"] = hs

    st.subheader("📋 Extracted Customs Information")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sender Name", invoice_data.get("sender_name") or "❓")
        st.metric("Sender EORI", invoice_data.get("sender_eori") or "Not found")
        if invoice_data.get("sender_siren"):
            st.caption(f"SIREN: {invoice_data['sender_siren']}")
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
    st.info("👈 Upload an invoice to begin.")
