# app/services/ocr_service.py

import os
import base64
from openai import OpenAI
from dotenv import load_dotenv
from app.services.supabase_client import supabase

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DOCUMENTS_ROOT = os.path.join("backend", "documents", "id")


def extract_text_from_user_documents(user_email: str) -> str:
    """
    Perform OCR using GPT-4o on all image documents for a user.
    Saves the extracted results to 'ocr-res.txt' under the same folder.
    """
    user_folder = os.path.join(DOCUMENTS_ROOT, user_email)
    if not os.path.exists(user_folder):
        raise FileNotFoundError(f"[ERROR] No folder found for user: {user_folder}")

    # Check for required documents before OCR
    files = set(f.lower() for f in os.listdir(user_folder))
    has_commercial = any(f in files for f in ["commercial.png", "commercial.jpg"])
    has_eid = any(f in files for f in ["eid.png", "eid.jpg"])
    if not (has_commercial and has_eid):
        raise Exception("[ERROR] OCR cannot be performed until both commercial and eid documents are present.")

    result_text = ""

    for filename in os.listdir(user_folder):
        file_path = os.path.join(user_folder, filename)

        if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue  # Skip non-image files

        print(f"[INFO] Processing file: {filename}")

        with open(file_path, "rb") as img_file:
            image_bytes = img_file.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "You are smart OCR enginer which is an expert in extracting text from official document images. Classify the documents based on theor tiles and extract all the relevant fields along with their values."},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                        ]
                    }
                ],
                max_tokens=2000
            )

            extracted = response.choices[0].message.content.strip()
            result_text += f"--- {filename} ---\n{extracted}\n\n"

        except Exception as e:
            result_text += f"--- {filename} ---\n[ERROR extracting text: {str(e)}]\n\n"
            print(f"[ERROR] Failed to process {filename}: {e}")

    # Save all extracted text to ocr-res.txt under user folder
    output_file = os.path.join(user_folder, "ocr-res.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result_text)

    print(f"[INFO] OCR results saved to: {output_file}")

    # ✅ Set onboarding_step to verification_complete before returning
    supabase.table("users").update({"onboarding_step": "verification_complete"}).eq("email", user_email).execute()
    print(f"[INFO] Onboarding step set to verification_complete for {user_email}")

    return output_file
