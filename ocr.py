import easyocr
import cv2
import json
from pprint import pprint

def preprocess_image(image_path: str, output_path: str = "processed_image.png") -> str:
    """
    Load the image, convert to grayscale, and resize for better OCR accuracy.
    """
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
    cv2.imwrite(output_path, resized)
    return output_path


def extract_text(image_path: str) -> list:
    """
    Perform OCR using EasyOCR.
    """
    reader = easyocr.Reader(['en'])  # Add 'ar' if you want to process Arabic as well
    results = reader.readtext(image_path, detail=0)  # detail=0 returns just text
    return results


def format_ocr_results(lines: list) -> dict:
    """
    Structure the OCR text into a key-value dictionary based on common field names.
    """
    data = {}
    fields = {
        'License No.': 'license_no',
        'Company Name': 'company_name',
        'Business Name': 'business_name',
        'License Category': 'license_category',
        'Legal Type': 'legal_type',
        'Expiry Date': 'expiry_date',
        'Issue Date': 'issue_date',
        'Register No.': 'register_no',
        'Nationality': 'nationality',
        'Shares Owner': 'owner_name',
        'Name': 'person_name',
    }

    for idx, line in enumerate(lines):
        for key, field_name in fields.items():
            if key.lower() in line.lower():
                try:
                    data[field_name] = lines[idx + 1]
                except IndexError:
                    data[field_name] = "Not found"
    return data


def save_to_json(data: dict, output_file: str):
    """
    Save the structured data to a JSON file.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"[✅] Extracted data saved to: {output_file}")


if __name__ == "__main__":
    # Input image file
    input_image = "Screenshot 2025-07-09 143837.png"

    # Step 1: Preprocess the image
    processed_image = preprocess_image(input_image)

    # Step 2: Perform OCR
    ocr_lines = extract_text(processed_image)
    print("[🔍] OCR Lines:")
    pprint(ocr_lines)

    # Step 3: Format structured data
    structured = format_ocr_results(ocr_lines)
    print("\n[📄] Structured Data:")
    pprint(structured)

    # Step 4: Save to JSON file
    save_to_json(structured, "extracted_license_data.json")
