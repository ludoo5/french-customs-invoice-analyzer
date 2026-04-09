from groq import Groq
import json
import re

CUSTOMS_PROMPT = """
You are an expert in French customs and invoice analysis.
Extract the following fields from the invoice text. 
Return ONLY a valid JSON object. Do not include any explanations, markdown, or extra text.

Fields to output (use null for missing):
{
  "sender_name": "string or null",
  "sender_eori": "string or null",
  "sender_siren": "string or null",
  "receiver_name": "string or null",
  "receiver_eori": "string or null",
  "receiver_country": "string or null",
  "document_number": "string or null",
  "type_of_shipment": "B2B" or "B2C" or "C2B" or "C2C" or null,
  "value": number or null,
  "airport_code": null,
  "commodities": [
    {
      "description_original": "string",
      "common_name_en": "string",
      "material": "string or null",
      "quantity": number,
      "hs_code": "string or null",
      "country_of_origin": "string or null"
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
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a JSON-only invoice parser. Output nothing but the JSON object."},
                {"role": "user", "content": CUSTOMS_PROMPT.format(text=text[:12000])}
            ],
            temperature=0,
            response_format={"type": "json_object"}  # This forces JSON output (Groq supports it)
        )
        content = response.choices[0].message.content

        # Try to parse directly
        return json.loads(content)

    except json.JSONDecodeError as e:
        # If direct parsing fails, try to extract JSON between first { and last }
        try:
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                json_str = content[start:end+1]
                return json.loads(json_str)
        except:
            pass
        # Return error with raw response
        raw = content if 'content' in locals() else "No response"
        return {"error": f"JSON parse error: {str(e)}", "raw_response": raw[:1000]}
    except Exception as e:
        return {"error": str(e)}
