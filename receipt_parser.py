from openai import OpenAI
import base64
import json
import fitz  # PyMuPDF
import re
from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)

EXTRACTION_PROMPT = """You are a receipt data extractor. Extract the following from this receipt and return ONLY valid JSON, nothing else.

{
  "vendor": "store or business name",
  "amount": 00.00,
  "date": "YYYY-MM-DD",
  "category": one of ["Food & Dining", "Travel", "Software & Subscriptions", "Office Supplies", "Equipment", "Utilities", "Other"],
  "confidence": one of ["HIGH", "MEDIUM", "LOW"],
  "notes": "any important details or why confidence is low"
}

Rules:
- amount must be the FINAL total (not subtotal). If multiple amounts, pick the largest labeled 'Total' or 'Grand Total'.
- If you cannot read a field clearly, set confidence to LOW and explain in notes.
- Never guess. If truly unreadable, set field to null.
- Return ONLY the JSON object, no other text."""

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract raw text from PDF using PyMuPDF - YOUR CODE, not AI"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

def pdf_to_image_base64(file_bytes: bytes) -> str:
    """Convert first page of PDF to image for GPT vision"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    return base64.b64encode(img_bytes).decode("utf-8")

def image_to_base64(file_bytes: bytes) -> str:
    """Convert image to base64"""
    return base64.b64encode(file_bytes).decode("utf-8")

def safe_extract_json(raw_response: str) -> dict:
    """Best-effort JSON extraction for model output."""
    text = (raw_response or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    return {
        "vendor": None,
        "amount": None,
        "date": None,
        "category": "Other",
        "confidence": "LOW",
        "notes": "Could not parse receipt JSON",
    }


def call_gpt_extraction(raw_text: str | None = None, image_b64: str | None = None, media_type: str = "image/png") -> str:
    content = [{"type": "input_text", "text": EXTRACTION_PROMPT}]
    if raw_text:
        content.append({"type": "input_text", "text": f"Receipt text:\n{raw_text}"})
    if image_b64:
        content.append({"type": "input_image", "image_url": f"data:{media_type};base64,{image_b64}"})

    response = client.responses.create(
        model="gpt-5",
        input=[{"role": "user", "content": content}],
        max_output_tokens=500,
    )
    return response.output_text


def parse_receipt_with_gpt(file_bytes: bytes, filename: str) -> dict:
    """
    AI LAYER: GPT extracts structured data from unstructured receipt.
    This is the ONLY place we call AI in the parsing pipeline.
    """
    is_pdf = filename.lower().endswith(".pdf")

    if is_pdf:
        # Try text extraction first (faster, cheaper)
        raw_text = extract_text_from_pdf(file_bytes)
        if len(raw_text) > 50:
            raw_response = call_gpt_extraction(raw_text=raw_text)
        else:
            # Fallback to vision for scanned PDFs.
            img_b64 = pdf_to_image_base64(file_bytes)
            raw_response = call_gpt_extraction(image_b64=img_b64, media_type="image/png")
        raw_text_for_storage = raw_text
    else:
        # Image receipt - use vision directly.
        img_b64 = image_to_base64(file_bytes)
        media_type = "image/jpeg" if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg") else "image/png"
        raw_response = call_gpt_extraction(image_b64=img_b64, media_type=media_type)
        raw_text_for_storage = ""

    # Parse GPT response safely and enforce required schema keys.
    data = safe_extract_json(raw_response)
    strict_defaults = {
        "vendor": None,
        "amount": None,
        "date": None,
        "category": "Other",
        "confidence": "LOW",
        "notes": "",
    }
    for key, fallback in strict_defaults.items():
        if key not in data:
            data[key] = fallback

    data["raw_text"] = raw_text_for_storage
    return data
