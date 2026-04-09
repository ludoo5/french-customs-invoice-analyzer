from groq import Groq
import json
import re

CUSTOMS_PROMPT = """
You are an expert in French customs and invoice analysis.
Extract the following fields from the invoice text. Return ONLY valid JSON.
If a field is not present, set it to null.

IMPORTANT RULES:
- sender_eori: extract any tax ID / EORI / VAT number exactly as written on the invoice.
  It can start with FR, BE, DE, NL, etc., or be a plain number. Do not modify it.
  If the invoice shows no tax ID for the sender, set sender_eori = null.
- For C2C (consumer to consumer) shipments, sender_eori and receiver_eori can be null – no need to search.
- type_of_shipment: determine from context (B2B, B2C, C2B, C2C). If both names look like individuals → C2C.
- value: Calculate VAT‑free total = (sum of merchandise net prices) + shipping (VAT-free) - discounts + deposit.
- commodities: For each line item, provide common English name and material.

Fields:
{
  "sender_name": str,
  "sender_eori": str or null,
  "sender_siren": str or null,
  "receiver_name": str,
  "receiver_eori": str or null,
  "receiver_country": str or null,
  "document_number": str,
  "type_of_shipment": "B2B" | "B2C" | "C2B" | "C2C" | null,
  "value": float or null,
  "airport_code": null,
  "commodities": [
    {
      "description_original": str,
      "common_name_en": str,
      "material": str or null,
      "quantity": float,
      "hs_code": str or null,
      "country_of_origin": str or null
    }
  ]
}

Invoice text:
{text}
"""

def analyze_invoice(text, api_key):
    client = Groq(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a customs invoice parser. Return ONLY valid JSON."},
                {"role": "user", "content": CUSTOMS_PROMPT.format(text=text[:12000])}
            ],
            temperature=0
        )
        content = response.choices[0].message.content

        # Clean markdown and extract JSON between first { and last }
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = content[start:end+1]
            return json.loads(json_str)
        else:
            return json.loads(content)
    except Exception as e:
        return {"error": str(e)}
