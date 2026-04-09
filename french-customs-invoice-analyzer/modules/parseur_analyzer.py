import streamlit as st
import requests
import time

def analyze_invoice_with_parseur(file_bytes, mailbox_id, api_key):
    """
    Upload an invoice to Parseur and wait for the extracted data.
    Returns a dictionary matching the required schema, or None on failure.
    """
    # 1. Upload document
    upload_url = f"https://api.parseur.com/parser/{mailbox_id}/upload"
    headers = {"Authorization": f"Token {api_key}"}
    files = {'file': file_bytes}
    
    try:
        response = requests.post(upload_url, headers=headers, files=files)
        response.raise_for_status()
        doc = response.json()
        
        # Extract DocumentID from the attachments list
        attachments = doc.get('attachments', [])
        if not attachments:
            st.error("No attachments returned from Parseur.")
            return None
        doc_id = attachments[0].get('DocumentID')
        if not doc_id:
            st.error("Parseur did not return a DocumentID.")
            return None
    except Exception as e:
        st.error(f"Upload to Parseur failed: {e}")
        if 'response' in locals():
            st.text(f"Status code: {response.status_code}")
            st.text(f"Response text: {response.text}")
        return None

    # 2. Poll for processing result
    result_url = f"https://api.parseur.com/api/documents/{doc_id}"
    with st.spinner("Processing with Parseur (up to 30 seconds)..."):
        for _ in range(30):
            try:
                res = requests.get(result_url, headers=headers)
                res.raise_for_status()
                data = res.json()
                status = data.get('status')
                if status == 'processed':
                    parsed = data.get('parsed', {})
                    return _format_result(parsed)
                elif status == 'failed':
                    st.error("Parseur failed to process the invoice.")
                    return None
                time.sleep(1)
            except Exception as e:
                st.error(f"Error while polling Parseur: {e}")
                return None
    st.error("Parseur processing timed out after 30 seconds.")
    return None

def _format_result(parsed):
    """Convert Parseur's output to the schema expected by the app."""
    commodities = []
    table = parsed.get('commodities', {}).get('value', [])
    for item in table:
        commodities.append({
            "description_original": item.get('description_original', {}).get('value'),
            "common_name_en": item.get('common_name_en', {}).get('value'),
            "material": item.get('material', {}).get('value'),
            "quantity": item.get('quantity', {}).get('value'),
            "hs_code": item.get('hs_code', {}).get('value'),
            "country_of_origin": item.get('country_of_origin', {}).get('value')
        })

    return {
        "sender_name": parsed.get('sender_name', {}).get('value'),
        "sender_eori": parsed.get('sender_eori', {}).get('value'),
        "sender_siren": parsed.get('sender_siren', {}).get('value'),
        "receiver_name": parsed.get('receiver_name', {}).get('value'),
        "receiver_eori": parsed.get('receiver_eori', {}).get('value'),
        "receiver_country": parsed.get('receiver_country', {}).get('value'),
        "document_number": parsed.get('document_number', {}).get('value'),
        "type_of_shipment": parsed.get('type_of_shipment', {}).get('value'),
        "value": parsed.get('value', {}).get('value'),
        "airport_code": None,
        "commodities": commodities
    }
