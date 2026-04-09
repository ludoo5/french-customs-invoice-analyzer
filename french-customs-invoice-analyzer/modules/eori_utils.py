import re
from .web_search import search_text

def find_eori_from_siren(siren):
    query = f"EORI number for French company SIREN {siren}"
    results = search_text(query, max_results=3)
    for res in results:
        match = re.search(r"(FR\d{12})", res)
        if match:
            return match.group(1)
    return None

def find_eori_from_name_and_postal(company_name, postal_code):
    query = f"{company_name} {postal_code} EORI number"
    results = search_text(query, max_results=3)
    for res in results:
        match = re.search(r"(FR\d{12})", res)
        if match:
            return match.group(1)
    return None
