import streamlit as st
import json
from modules.parseur_analyzer import analyze_invoice_with_parseur

# Optional web search modules – keep commented out unless you have them
# from modules.web_search import search_text
# from modules.eori_utils import find_eori_from_siren, find_eori_from_name_and_postal
# from modules.airport_codes import get_airport_code
# from modules.hs_resolver import get_hs_code_for_commodity

st.set_page_config(page_title="French Customs Invoice Analyzer", layout="wide")
st.title("📑 French Customs Invoice Analyzer")
st.markdown("Upload an invoice – Parseur extracts all customs fields automatically.")

with st.sidebar:
    st.header("🔑 Configuration")
    
    # Parseur credentials
    parseur_api_key = st.secrets.get("PARSEUR_API_KEY", "")
    if not parseur_api_key:
        parseur_api_key = st.text_input("Parseur API Key", type="password",
                                        help="Get from your Parseur account settings")
    
    parseur_mailbox_id = st.secrets.get("PARSEUR_MAILBOX_ID", "")
    if not parseur_mailbox_id:
        parseur_mailbox_id = st.text_input("Parseur Mailbox ID",
                                           help="The numeric ID from your mailbox URL (e.g., 177528)")
    
    use_web_search = st.checkbox("Enable Web Search (optional)", value=False,
                                 help="Requires additional modules – keep off if not needed")
    
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload invoice", type=["pdf", "png", "jpg", "jpeg"])

# Main processing
if uploaded_file and parseur_api_key and parseur_mailbox_id:
    file_bytes = uploaded_file.read()
    
    with st.spinner("Sending to Parseur for analysis..."):
        # Call the function with all three arguments
        invoice_data = analyze_invoice_with_parseur(file_bytes, parseur_mailbox_id, parseur_api_key)
    
    if invoice_data is None:
        st.error("Parseur analysis failed. Check your API key, mailbox ID, and invoice format.")
        st.stop()
    
    # Optional web search enrichment (disabled by default)
    if use_web_search:
        st.info("Web search is disabled in this version. Enable it by uncommenting imports and adding code.")
    
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
        st.metric("VAT‑Free Value (€)", f"{value:,.2f}" if value else "Not found")
    
    st.subheader("📦 Commodities")
    if invoice_data.get("commodities"):
        st.dataframe(invoice_data["commodities"])
    else:
        st.info("No line items found.")
    
    st.download_button(
        "💾 Download JSON Report",
        data=json.dumps(invoice_data, indent=2, ensure_ascii=False),
        file_name="customs_invoice_report.json",
        mime="application/json"
    )

elif uploaded_file and (not parseur_api_key or not parseur_mailbox_id):
    st.warning("⚠️ Please provide both Parseur API Key and Mailbox ID in the sidebar.")
else:
    st.info("👈 Upload an invoice and enter your Parseur credentials to begin.")
