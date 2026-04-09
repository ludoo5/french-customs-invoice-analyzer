# Enrich sender EORI if missing but SIREN exists
if not invoice_data.get("sender_eori") and invoice_data.get("sender_siren"):
    eori = find_eori_from_siren(invoice_data["sender_siren"])
    if eori:
        invoice_data["sender_eori"] = eori

# Try to find EORI from company name if still missing
if not invoice_data.get("sender_eori") and invoice_data.get("sender_name"):
    postal_match = re.search(r'\b(\d{5})\b', raw_text)
    postal_code = postal_match.group(1) if postal_match else None
    if postal_code:
        eori = find_eori_from_name_and_postal(invoice_data["sender_name"], postal_code)
        if eori:
            invoice_data["sender_eori"] = eori
