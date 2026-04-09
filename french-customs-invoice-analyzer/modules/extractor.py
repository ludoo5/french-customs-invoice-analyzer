import pdfplumber
import easyocr
from PIL import Image
import io
import numpy as np

# Initialize EasyOCR reader once (French + English)
reader = easyocr.Reader(['fr', 'en'], gpu=False)

def extract_text_from_pdf(file_bytes):
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        text = f"Error extracting PDF text: {str(e)}"
    return text

def extract_text_from_image(file_bytes):
    try:
        # Open image with PIL
        image = Image.open(io.BytesIO(file_bytes))
        # Convert PIL image to numpy array (EasyOCR expects numpy array)
        image_np = np.array(image)
        # Perform OCR
        result = reader.readtext(image_np, detail=0, paragraph=True)
        text = " ".join(result)
        return text
    except Exception as e:
        return f"Error extracting image text: {str(e)}"
