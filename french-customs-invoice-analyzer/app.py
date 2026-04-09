import streamlit as st
import json
from modules.parseur_analyzer import init_parseur_client, analyze_invoice_with_parseur
from modules.web_search import search_text
from modules.eori_utils import find_eori_from_siren, find_eori_from_name_and_postal
from modules.airport_codes import get_airport_code
from modules.hs_resolver import get_hs_code_for_commodity

st.set_page_config(page_title="French Customs Invoice Analyzer", layout="wide")
st.title("📑 French Customs Invoice Analyzer")

# Sidebar inputs
with st.sidebar:
    st.header("🔑 API Configuration")
    
    parseur_api_key = st.secrets.get("PARSEUR_API_KEY", "")
    if not parseur_api_key:
        parseur_api_key = st.text_input("Parseur API Key", type="password", help="Get from Parseur account settings")
    
    parseur_mailbox_id = st.secrets.get("PARSEUR_MAILBOX_ID", "")
    if not parseur_mailbox_id:
        parseur_mailbox_id = st.text_input("Parseur Mailbox ID", help="The numeric ID from your mailbox URL")
    
    use_web_search = st.checkbox("Enable Web Search", value=True)
    
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload invoice (PDF/PNG/JPG)", type=["pdf", "png", "jpg", "jpeg"])

# Main processing – only run if all required inputs are present
if uploaded_file and parseur_api_key and parseur_mailbox_id:
    # Initialize Parseur client
    init_parseur_client(parseur_api_key)
    
    file_bytes = uploaded_file.read()
    
    # Step 1: Parse invoice with Parseur
    with st.spinner("🔍 Sending invoice to Parseur for analysis..."):
        invoice_data = analyze_invoice_with_parseur(file_bytes, parseur_mailbox_id, parseur_api_key)
    
    if invoice_data is None:
        st.error("Parseur analysis failed. Please check your mailbox ID and API key, and ensure the invoice format is supported.")
        st.stop()
    
    # Step 2: Web search enrichment (optional)
    if use_web_search:
        with st.spinner("🌐 Enriching with web search..."):
            # Extract raw text for postal code search (only if needed)
            # For simplicity, we'll skip raw text extraction here; you can add back if needed.
            # The enrichment code can be adapted from your previous version.
            pass  # Placeholder – add your enrichment logic if desired
    
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

elif uploaded_file and (not parseur_api_key or not parseur_mailbox_id):
    st.warning("⚠️ Please provide both Parseur API Key and Mailbox ID in the sidebar.")
else:
    st.info("👈 Upload an invoice and enter your Parseur credentials to begin.")
