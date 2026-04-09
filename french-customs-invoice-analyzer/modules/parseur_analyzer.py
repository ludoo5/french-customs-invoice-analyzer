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
        # 1. Upload the document to your specified mailbox
        # The library expects the mailbox ID as an integer
        document = parseur.Document.create(mailbox_id=int(mailbox_id), file=file_bytes)
        document_id = document['id']

        # 2. Poll the API until the document is processed
        with st.spinner('Sending invoice to Parseur for analysis...'):
            status = None
            parsed_result = None
            # Give Parseur up to 30 seconds to process (adjust as needed)
            for _ in range(30):
                # Fetch the latest status of the document
                doc_status = parseur.Document.retrieve(id=document_id)
                status = doc_status['status']
                if status == 'processed':
                    # 'parsed' contains the extracted data in your schema
                    parsed_result = doc_status['parsed']
                    break
                elif status == 'failed':
                    st.error(f"Parseur failed to process the document. Status: {status}")
                    return None
                time.sleep(1)  # Wait 1 second before checking again

            if parsed_result:
                # Convert the result to match your app's expected format
                return format_parseur_result(parsed_result)
            else:
                st.error(f"Parseur processing timed out. Final status: {status}")
                return None

    except Exception as e:
        st.error(f"An error occurred with the Parseur API: {e}")
        return None

def format_parseur_result(parsed_data):
    """Maps Parseur's output keys to your app's expected JSON structure."""
    # This function adapts Parseur's field names to your schema.
    # Adjust the keys based on exactly what you named your fields in Parseur.
    commodities = []
    # Parseur's table data is often found under a key that matches your table's name.
    # You will need to inspect `parsed_data` to find the exact key.
    # For the sake of example, let's assume your table field is named 'commodities'.
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
        "airport_code": None, # Your web search module will fill this
        "commodities": commodities
    }
