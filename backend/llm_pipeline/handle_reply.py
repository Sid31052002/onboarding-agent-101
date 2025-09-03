# backend/llm_pipeline/handle_reply.py

from ingestion.faq_retriever import retrieve_similar_chunks
from llm_runner.prompt_templates import build_onboarding_prompt
from llm_runner.run_model import call_local_llm
from app.services.supabase_client import supabase
from app.services.email_sender import send_email
from app.services.ocr_service import process_document

from datetime import datetime
import os
import time
import json

def check_documents_in_ocr(ocr_results: dict) -> dict:
    """
    Checks OCR results for presence of commercial and eid documents.
    ocr_results: dict with format {'filename': {'type': 'commercial'/'eid'/'unknown', 'text': 'extracted_text'}}
    Returns a dict: {'commercial': bool, 'eid': bool, 'missing': list}
    """
    has_commercial = False
    has_eid = False
    
    for filename, data in ocr_results.items():
        doc_type = data.get('type', 'unknown')
        if doc_type == 'commercial':
            has_commercial = True
        elif doc_type == 'eid':
            has_eid = True
    
    missing = []
    if not has_commercial:
        missing.append("Commercial Registration Document")
    if not has_eid:
        missing.append("Resident Identity Card (EID)")
    
    return {
        "commercial": has_commercial, 
        "eid": has_eid,
        "missing": missing
    }

def process_user_reply(from_email: str, body: str, attachments: list = None):
    # `Step 1: Get the user
    user_response = supabase.table("users").select("*").eq("email", from_email).execute()
    if not user_response.data or len(user_response.data) == 0:
        print(f"[WARN] Email not found in users table: {from_email}")
        return

    user = user_response.data[0]

    # Save attachments to backend/documents/id/{email}/
    if attachments:
        print(f"[DEBUG] Attachments received: {[a['filename'] for a in attachments]}")
        save_dir = os.path.join("backend", "documents", "id", from_email)
        os.makedirs(save_dir, exist_ok=True)
        
        image_files_saved = []
        for a in attachments:
            filename = a["filename"]
            filedata = a["data"]
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                filepath = os.path.join(save_dir, filename)
                print(f"[DEBUG] Saving image attachment: {filepath} (size: {len(filedata)} bytes)")
                with open(filepath, "wb") as f:
                    f.write(filedata)
                image_files_saved.append(filename)
            else:
                print(f"[WARN] Skipping non-image file: {filename}")
        
        if not image_files_saved:
            subject = "No Valid Documents Received"
            body = "Please attach image files (PNG, JPG, JPEG, WEBP) containing your Commercial Registration Document and Resident Identity Card (EID)."
            send_email(to_email=from_email, subject=subject, body=body)
            print(f"[WARN] No image files found in attachments for: {from_email}")
            return
        
        supabase.table("users").update({"onboarding_step": "document_verification"}).eq("email", from_email).execute()
        print("[INFO] Running OCR for uploaded documents...")

        # Run OCR for each image using process_document
        for filename in image_files_saved:
            document_id = os.path.splitext(filename)[0]
            file_path = os.path.join(save_dir, filename)
            try:
                process_document(from_email, document_id, file_path)
            except Exception as e:
                print(f"[ERROR] OCR failed for {filename}: {e}")

        # Now extract structured OCR results
        try:
            # Gather OCR results from output.json files for each image
            ocr_results = {}
            for filename in image_files_saved:
                document_id = os.path.splitext(filename)[0]
                output_path = os.path.join(save_dir, document_id, "output.json")
                if os.path.exists(output_path):
                    with open(output_path, "r", encoding="utf-8") as f:
                        analysis = json.load(f)
                    ocr_results[filename] = {
                        "type": analysis.get("document_type", "unknown"),
                        "raw_text": analysis.get("raw_text", ""),
                        "status_message": analysis.get("status_message", ""),
                        "extracted_fields": analysis.get("extracted_fields", {}),
                        "validation": analysis.get("validation", {}),
                        "is_valid": analysis.get("is_valid", False)
                    }
                else:
                    ocr_results[filename] = {
                        "type": "error",
                        "raw_text": "",
                        "status_message": "❌ ERROR: No OCR output found.",
                        "extracted_fields": {},
                        "validation": {},
                        "is_valid": False
                    }
            # --- NEW LOGIC: Aggregate previous documents ---
            user_docs_dir = os.path.join("backend", "documents", "id", from_email)
            if os.path.exists(user_docs_dir):
                for doc_dir in os.listdir(user_docs_dir):
                    output_path = os.path.join(user_docs_dir, doc_dir, "output.json")
                    if os.path.exists(output_path):
                        with open(output_path, "r", encoding="utf-8") as f:
                            analysis = json.load(f)
                        # Use doc_dir as key to avoid filename collision
                        ocr_results[doc_dir] = {
                            "type": analysis.get("document_type", "unknown"),
                            "raw_text": analysis.get("raw_text", ""),
                            "status_message": analysis.get("status_message", ""),
                            "extracted_fields": analysis.get("extracted_fields", {}),
                            "validation": analysis.get("validation", {}),
                            "is_valid": analysis.get("is_valid", False)
                        }
            print(f"[INFO] OCR completed for {len(ocr_results)} documents")

            # Check OCR results for required documents
            doc_status = check_documents_in_ocr(ocr_results)
            
            # Identify wrongly submitted documents
            wrong_docs = [
                (filename, data.get("type", "unknown"))
                for filename, data in ocr_results.items()
                if data.get("type") == "unknown"
            ]
            
            if not doc_status["missing"] and not wrong_docs:
                subject = "Documents Received and Verified"
                body = "Great! Both your Commercial Registration Document and Resident Identity Card (EID) have been successfully received and verified. Your onboarding will proceed to the next step."
            else:
                subject = "Missing or Incorrect Document(s)"
                body = "We have processed your submitted documents.\n\n"
                if doc_status["missing"]:
                    body += "We still need the following:\n"
                    for missing_doc in doc_status["missing"]:
                        body += f"• {missing_doc}\n"
                if wrong_docs:
                    body += "\nThe following document(s) you submitted are not required or could not be recognized:\n"
                    for filename, doc_type in wrong_docs:
                        doc_info = ocr_results.get(filename, {})
                        status_message = doc_info.get("status_message", "")
                        raw_text = doc_info.get("raw_text", "")
                        body += (
                            f"• {filename}: {status_message}\n"
                            "Extracted text from your document:\n"
                            f"{raw_text}\n"
                            "Please submit only your Commercial Registration Document and Resident Identity Card (EID) containing the required fields.\n"
                        )
                body += "\nPlease reply to this email with the correct document(s) attached as image files."

            send_email(to_email=from_email, subject=subject, body=body)
            print(f"[INFO] Document verification result sent to: {from_email}")

            # If missing or wrong documents, don't proceed further
            if doc_status["missing"] or wrong_docs:
                return

        except Exception as e:
            print(f"[ERROR] OCR failed for {from_email}: {e}")
            subject = "Error Processing Your Documents"
            body = f"We encountered an error while processing your documents. Please ensure your images are clear and readable, then try submitting them again.\n\nError details: {str(e)}"
            send_email(to_email=from_email, subject=subject, body=body)
            return

    # Step 2: Log user message in conversation
    supabase.table("conversations").insert({
        "user_email": from_email,
        "role": "user",
        "message": body,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

    # Step 3: Search FAQ for context
    top_chunks = retrieve_similar_chunks(body, top_k=3)
    faq_context = "\n\n".join(top_chunks)

    # Step 3.1: Get conversation history for context
    convo_response = supabase.table("conversations").select("*").eq("user_email", from_email).order("timestamp").execute()
    convo_history = convo_response.data if convo_response.data else []
    convo_context = "\n".join([f"{msg['role']}: {msg['message']}" for msg in convo_history])

    # dd onboarding_step to context
    onboarding_step = user.get("onboarding_step", "welcome")
    full_context = f"Onboarding Step: {onboarding_step}\n\n{convo_context}\n\nFAQ:\n{faq_context}"

    # Step 4: Build prompt and call LLM with both contexts
    prompt = build_onboarding_prompt(user_message=body, context=full_context)

    llm_response = call_local_llm(prompt)

    # Step 5: Send reply
    subject = "Re: Your query with Thrivv"
    send_email(to_email=from_email, subject=subject, body=llm_response)

    #  Step 6: Log agent message in conversation
    supabase.table("conversations").insert({
        "user_email": from_email,
        "role": "agent",
        "message": llm_response,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

    print(f"[INFO] Replied to: {from_email}")