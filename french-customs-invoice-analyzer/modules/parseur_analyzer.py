# modules/parseur_analyzer.py
import streamlit as st
import requests
import time
import json

def analyze_invoice_with_parseur(file_bytes, mailbox_id, api_key):
    """
    Uploads an invoice file to a Parseur mailbox via the API and polls for the parsed result.
    """
    # 1. Upload the document to Parseur
    upload_url = f"https://api.parseur.com/api/mailboxes/{mailbox_id}/documents"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/octet-stream"
    }
    try:
        # Upload the file as binary data in the request body
        upload_response = requests.post(upload_url, headers=headers, data=file_bytes)
        upload_response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        document_data = upload_response.json()
        document_id = document_data.get('id')
        if not document_id:
            st.error("Failed to get document ID from Parseur response.")
            return None

        st.success(f"Document uploaded successfully. Processing...")

    except requests.exceptions.RequestException as e:
        st.error(f"Error uploading to Parseur: {e}")
        if 'upload_response' in locals():
            st.text(f"Response status code: {upload_response.status_code}")
            st.text(f"Response body: {upload_response.text}")
        return None

    # 2. Poll for the result
    result_url = f"https://api.parseur.com/api/documents/{document_id}"
    with st.spinner('Waiting for Parseur to process the invoice...'):
        for _ in range(30):  # Wait up to 30 seconds
            try:
                result_response = requests.get(result_url, headers=headers)
                result_response.raise_for_status()
                doc_status = result_response.json()
                status = doc_status.get('status')
                if status == 'processed':
                    parsed_result = doc_status.get('parsed')
                    if parsed_result:
                        st.success("Invoice processed successfully.")
                        # Format the result to match your app's expected schema
                        return format_parseur_result(parsed_result)
                    else:
                        st.error("Parseur processed the document but returned no parsed data.")
                        return None
                elif status == 'failed':
                    st.error("Parseur failed to process the document.")
                    return None
                time.sleep(1)
            except requests.exceptions.RequestException as e:
                st.error(f"Error polling Parseur for result: {e}")
                return None

    st.error("Parseur processing timed out.")
    return None

def format_parseur_result(parsed_data):
    """Map Parseur's output to your app's JSON structure."""
    # This is a generic mapping. Adjust the keys based on your actual field names in Parseur.
    # The `parsed_data` from Parseur is a dictionary where the keys are the field names
    # you defined, and the values are dictionaries with a "value" key.
    commodities = []
    # Assuming your table field is named 'commodities'
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
