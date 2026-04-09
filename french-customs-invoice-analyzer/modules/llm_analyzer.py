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
- type_of_shipment: determine from context (B2B, B2C, C2B, C2C).
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
  "type_of_shipment": str or null,
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
            model="llama-3.1-8b-instant",  # switched to more stable model
            messages=[
                {"role": "system", "content": "You are a customs invoice parser. Return ONLY valid JSON. Do not include any other text, explanations, or markdown."},
                {"role": "user", "content": CUSTOMS_PROMPT.format(text=text[:12000])}
            ],
            temperature=0
        )
        content = response.choices[0].message.content

        # Clean the response: remove markdown code blocks and any text outside JSON
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        
        # Find the first '{' and the last '}' to extract pure JSON
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = content[start:end+1]
            return json.loads(json_str)
        else:
            # If no braces found, try to parse whole content
            return json.loads(content)

    except json.JSONDecodeError as e:
        # Return the raw response so we can see it in the Streamlit error
        raw = content if 'content' in locals() else "No response content"
        return {"error": f"JSON parse error: {str(e)}", "raw_response": raw[:500]}
    except Exception as e:
        return {"error": str(e)}
