import base64
import json
import re
from groq import Groq

def analyze_invoice_image(image_bytes, api_key):
    """Send image directly to Groq Vision model and get structured data."""
    client = Groq(api_key=api_key)
    
    # Encode image to base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    prompt = """You are an expert in French customs and invoice analysis. 
Extract the following fields from the invoice image. Return ONLY a valid JSON object.
If a field is not present, set it to null.

Fields:
{
  "sender_name": string or null,
  "sender_eori": string or null,
  "sender_siren": string or null,
  "receiver_name": string or null,
  "receiver_eori": string or null,
  "receiver_country": string or null,
  "document_number": string or null,
  "type_of_shipment": "B2B" or "B2C" or "C2B" or "C2C" or null,
  "value": number or null,
  "airport_code": null,
  "commodities": [
    {
      "description_original": string,
      "common_name_en": string,
      "material": string or null,
      "quantity": number,
      "hs_code": string or null,
      "country_of_origin": string or null
    }
  ]
}

Important rules:
- sender_eori: any tax ID (EORI, VAT) – can start with BE, FR, etc.
- value: VAT‑free total in EUR (from invoice total)
- commodities: extract from the table – each row.
- type_of_shipment: B2B if both sender and receiver are businesses.

Invoice image attached."""
    
    try:
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        # Clean and parse JSON
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        return json.loads(content)
    except Exception as e:
        return {"error": str(e), "raw_response": content if 'content' in locals() else None}
