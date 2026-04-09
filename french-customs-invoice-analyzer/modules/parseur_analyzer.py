# modules/parseur_analyzer.py
import streamlit as st
import parseur
import time

@st.cache_resource
def init_parseur_client(api_key):
    """Initialize the Parseur client with your API key."""
    parseur.api_key = api_key

def analyze_invoice_with_parseur(file_bytes, mailbox_id):
    """
    Uploads an invoice file to a Parseur mailbox and polls for the parsed result.
    """
    try:
        # Upload the document
        document = parseur.Document.create(mailbox_id=int(mailbox_id), file=file_bytes)
        document_id = document['id']

        # Poll until processed
        with st.spinner('Waiting for Parseur to process the invoice...'):
            for _ in range(30):
                doc_status = parseur.Document.retrieve(id=document_id)
                status = doc_status['status']
                if status == 'processed':
                    parsed_result = doc_status['parsed']
                    break
                elif status == 'failed':
                    st.error(f"Parseur processing failed.")
                    return None
                time.sleep(1)
            else:
                st.error("Parseur processing timed out.")
                return None

        # Format the result to match your app's expected schema
        return format_parseur_result(parsed_result)

    except Exception as e:
        st.error(f"Parseur API error: {e}")
        return None

def format_parseur_result(parsed_data):
    """Map Parseur's output to your app's JSON structure."""
    commodities = []
    # Adjust the key names based on what you named your fields in Parseur
    table_data = parsed_data.get('commodities', {}).get('value', [])
    for item in table_data:
        commodities.append({
            "description_original": item.get('description_original', {}).get('value'),
            "common_name_en": item.get('common_name_en', {}).get('value'),
            "material": item.get('material', {}).get('value'),
            "quantity": item.get('quantity', {}).get('value'),
            "hs_code": item.get('hs_code', {}).get('value'),
            "country_of_origin": item.get('country_of_origin', {}).get('value')
        })

    return {
        "sender_name": parsed_data.get('sender_name', {}).get('value'),
        "sender_eori": parsed_data.get('sender_eori', {}).get('value'),
        "sender_siren": parsed_data.get('sender_siren', {}).get('value'),
        "receiver_name": parsed_data.get('receiver_name', {}).get('value'),
        "receiver_eori": parsed_data.get('receiver_eori', {}).get('value'),
        "receiver_country": parsed_data.get('receiver_country', {}).get('value'),
        "document_number": parsed_data.get('document_number', {}).get('value'),
        "type_of_shipment": parsed_data.get('type_of_shipment', {}).get('value'),
        "value": parsed_data.get('value', {}).get('value'),
        "airport_code": None,
        "commodities": commodities
    }
