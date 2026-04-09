import re
from .web_search import search_text

COUNTRY_AIRPORT_MAP = {
    "france": "CDG", "germany": "FRA", "united states": "JFK",
    "usa": "JFK", "china": "PVG", "united kingdom": "LHR",
    "italy": "FCO", "spain": "MAD", "netherlands": "AMS",
    "belgium": "BRU", "switzerland": "ZRH", "japan": "NRT"
}

def get_airport_code(country_name):
    if not country_name:
        return None
    country_lower = country_name.lower().strip()
    for key, code in COUNTRY_AIRPORT_MAP.items():
        if key in country_lower or country_lower in key:
            return code
    # Fallback web search
    query = f"main cargo airport IATA code {country_name}"
    results = search_text(query, max_results=2)
    for res in results:
        match = re.search(r'\b([A-Z]{3})\b', res)
        if match and match.group(1) not in ['THE', 'AND', 'FOR']:
            return match.group(1)
    return None
