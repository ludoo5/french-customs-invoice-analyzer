import re

def analyze_invoice(text, api_key=None):  # api_key no longer needed
    """
    Extract invoice fields using regex patterns.
    Returns a dictionary matching the required format.
    """
    result = {
        "sender_name": None,
        "sender_eori": None,
        "sender_siren": None,
        "receiver_name": None,
        "receiver_eori": None,
        "receiver_country": None,
        "document_number": None,
        "type_of_shipment": None,
        "value": None,
        "airport_code": None,
        "commodities": []
    }
    
    # 1. Sender name (common patterns)
    sender_patterns = [
        r'(?:Seller|Vendor|Sender|From|Expéditeur|Vendeur)\s*:?\s*([^\n]+)',
        r'(?:Company|Business)\s*:?\s*([^\n]+)',
    ]
    for pattern in sender_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["sender_name"] = match.group(1).strip()
            break
    
    # 2. Sender EORI (FR + 12 digits or BE + 12 digits, etc.)
    eori_match = re.search(r'\b([A-Z]{2}\d{12})\b', text)
    if eori_match:
        result["sender_eori"] = eori_match.group(1)
    
    # 3. Sender SIREN (9 digits, French)
    siren_match = re.search(r'\b(\d{9})\b', text)
    if siren_match:
        result["sender_siren"] = siren_match.group(1)
    
    # 4. Receiver name
    receiver_patterns = [
        r'(?:Buyer|Customer|Receiver|To|Destinataire|Client)\s*:?\s*([^\n]+)',
        r'(?:Ship to|Deliver to)\s*:?\s*([^\n]+)',
    ]
    for pattern in receiver_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["receiver_name"] = match.group(1).strip()
            break
    
    # 5. Receiver EORI / tax ID (any country code)
    tax_match = re.search(r'\b([A-Z]{2}\d{8,14})\b', text)
    if tax_match and tax_match.group(1) != result.get("sender_eori"):
        result["receiver_eori"] = tax_match.group(1)
    
    # 6. Document number (invoice, proforma, etc.)
    doc_patterns = [
        r'(?:Invoice|Facture|Proforma|Document)\s*(?:No|Number|N°|#)?\s*:?\s*([A-Z0-9\-]+)',
        r'\b(?:INV|INV-|INV/)([0-9\-]+)',
    ]
    for pattern in doc_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["document_number"] = match.group(1) if match.lastindex else match.group(0)
            break
    
    # 7. Total value (VAT-free) - look for total amounts
    amount_patterns = [
        r'Total\s*(?:HT|excl\.? VAT|without VAT|hors taxes?)\s*:?\s*([0-9,]+\.?[0-9]*)',
        r'Total\s*:?\s*([0-9,]+\.?[0-9]*)\s*(?:€|EUR|USD)',
        r'Montant\s*HT\s*:?\s*([0-9,]+\.?[0-9]*)',
    ]
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(',', '.')
            try:
                result["value"] = float(value_str)
                break
            except:
                pass
    
    # 8. Receiver country (look for country names or codes)
    country_match = re.search(r'\b(France|Germany|Belgium|Spain|Italy|UK|USA|China|Japan)\b', text, re.IGNORECASE)
    if country_match:
        result["receiver_country"] = country_match.group(1).title()
    
    # 9. Type of shipment (simple heuristic)
    text_lower = text.lower()
    if "b2b" in text_lower:
        result["type_of_shipment"] = "B2B"
    elif "b2c" in text_lower:
        result["type_of_shipment"] = "B2C"
    elif "c2c" in text_lower:
        result["type_of_shipment"] = "C2C"
    elif "c2b" in text_lower:
        result["type_of_shipment"] = "C2B"
    else:
        # Guess based on names (if one looks like a company, other like individual)
        if result["sender_name"] and ("SARL" in result["sender_name"] or "LTD" in result["sender_name"] or "INC" in result["sender_name"]):
            if result["receiver_name"] and not any(x in result["receiver_name"] for x in ["SARL", "LTD", "INC", "SAS", "SA"]):
                result["type_of_shipment"] = "B2C"
            else:
                result["type_of_shipment"] = "B2B"
        else:
            result["type_of_shipment"] = "C2C"
    
    # 10. Commodities (simple line items)
    # Look for lines with quantity, description, price
    lines = text.split('\n')
    for line in lines:
        # Pattern: quantity, then description, then price
        item_match = re.search(r'(\d+)\s+([A-Za-z0-9\s]+?)\s+([0-9,]+\.?[0-9]*)', line)
        if item_match:
            qty = int(item_match.group(1))
            desc = item_match.group(2).strip()
            price_str = item_match.group(3).replace(',', '.')
            try:
                unit_price = float(price_str)
                result["commodities"].append({
                    "description_original": desc,
                    "common_name_en": desc,  # will be refined by web search later
                    "material": None,
                    "quantity": qty,
                    "hs_code": None,
                    "country_of_origin": None
                })
            except:
                pass
    
    # If no commodities found, try a fallback: just take first few words as description
    if not result["commodities"]:
        # Try to find any product-like terms
        product_match = re.search(r'(?:Product|Item|Article|Description)\s*:?\s*([^\n]+)', text, re.IGNORECASE)
        if product_match:
            result["commodities"].append({
                "description_original": product_match.group(1).strip(),
                "common_name_en": product_match.group(1).strip(),
                "material": None,
                "quantity": 1,
                "hs_code": None,
                "country_of_origin": None
            })
    
    return result
