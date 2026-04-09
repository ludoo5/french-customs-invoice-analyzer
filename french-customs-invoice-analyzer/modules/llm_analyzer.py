import re

def analyze_invoice(text, api_key=None):
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
    
    # --- SENDER (From block) ---
    from_match = re.search(r'From\s*\n-+\s*\n.*?Name and address of sender\s*\n(.*?)(?=\n-|\nContact|\Z)', text, re.DOTALL | re.IGNORECASE)
    if from_match:
        sender_block = from_match.group(1)
        lines = sender_block.strip().split('\n')
        if lines:
            result["sender_name"] = lines[0].strip()
    
    # Sender VAT / EORI
    vat_match = re.search(r'VAT No\.:\s*([A-Z0-9]+)', text, re.IGNORECASE)
    if vat_match:
        result["sender_eori"] = vat_match.group(1)  # Use VAT as EORI if no separate EORI
    
    # --- RECEIVER (To block) ---
    to_match = re.search(r'To\s*\n-+\s*\n.*?Name and address of addressee\s*\n(.*?)(?=\n-|\nContact|\Z)', text, re.DOTALL | re.IGNORECASE)
    if to_match:
        receiver_block = to_match.group(1)
        lines = receiver_block.strip().split('\n')
        if lines:
            result["receiver_name"] = lines[0].strip()
            # Try to extract country from address (last line often)
            for line in lines[::-1]:
                if re.search(r'\b(Switzerland|France|Germany|Belgium|Italy|Spain)\b', line, re.IGNORECASE):
                    result["receiver_country"] = line.strip()
                    break
    
    # Receiver VAT / EORI
    receiver_vat_match = re.search(r'VAT No\.:\s*([A-Z0-9]+)', text, re.IGNORECASE)
    if receiver_vat_match and receiver_vat_match.group(1) != result.get("sender_eori"):
        result["receiver_eori"] = receiver_vat_match.group(1)
    
    # --- DOCUMENT NUMBER ---
    doc_match = re.search(r'Invoice\s*:\s*(\S+)', text, re.IGNORECASE)
    if doc_match:
        result["document_number"] = doc_match.group(1)
    
    # --- TOTAL VALUE ---
    total_match = re.search(r'Total value\s*\n-+\s*\n([0-9,]+)\s*EUR', text, re.IGNORECASE)
    if total_match:
        value_str = total_match.group(1).replace(',', '.')
        try:
            result["value"] = float(value_str)
        except:
            pass
    
    # --- COMMODITIES (table rows) ---
    # The table looks like: | Description | Quantity | Weight | Value | HS code | Origin |
    # We'll capture lines between the header and the "Totals" row.
    table_start = re.search(r'Description of content.*?Quantity.*?Weight.*?Value.*?HS tariff number.*?Country of origin', text, re.IGNORECASE | re.DOTALL)
    if table_start:
        # From that point, capture until "Totals"
        table_section = text[table_start.end():]
        totals_match = re.search(r'Totals', table_section, re.IGNORECASE)
        if totals_match:
            table_section = table_section[:totals_match.start()]
        # Split into lines
        lines = table_section.split('\n')
        for line in lines:
            # Each row: ski-boots    2    1    200.00    64021210    BE
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 6:
                desc = parts[0].strip()
                qty_str = parts[1].strip()
                value_str = parts[3].strip().replace(',', '.')
                hs_code = parts[4].strip()
                origin = parts[5].strip()
                try:
                    qty = float(qty_str) if '.' in qty_str else int(qty_str)
                except:
                    qty = 1
                try:
                    unit_value = float(value_str)
                except:
                    unit_value = None
                result["commodities"].append({
                    "description_original": desc,
                    "common_name_en": desc,
                    "material": None,
                    "quantity": qty,
                    "hs_code": hs_code if hs_code != '' else None,
                    "country_of_origin": origin if origin != '' else None
                })
    
    # --- SHIPMENT TYPE (B2B because both are companies) ---
    if "DHL Parcel" in result.get("sender_name", "") or "DHL Parcel" in result.get("receiver_name", ""):
        result["type_of_shipment"] = "B2B"
    elif result["sender_name"] and result["receiver_name"]:
        # Both look like businesses
        result["type_of_shipment"] = "B2B"
    else:
        result["type_of_shipment"] = "Unknown"
    
    # --- AIRPORT CODE (will be filled by web search later) ---
    # Keep as None for now, web search will set it.
    
    return result
