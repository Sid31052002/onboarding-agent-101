# backend/llm_pipeline/handle_reply.py

from ingestion.faq_retriever import retrieve_similar_chunks
from llm_runner.prompt_templates import build_onboarding_prompt
from llm_runner.run_model import call_local_llm
from app.services.supabase_client import supabase
from app.services.email_sender import send_email

from datetime import datetime
import os

def process_user_reply(from_email: str, body: str, attachments: list = None):
    # ✅ Step 1: Get the user
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
        for a in attachments:
            filename = a["filename"]
            filedata = a["data"]
            filepath = os.path.join(save_dir, filename)
            print(f"[DEBUG] Saving attachment: {filepath} (size: {len(filedata)} bytes)")
            with open(filepath, "wb") as f:
                f.write(filedata)

    # Check for required attachments
    required_files = {"commercial.png", "commercial.jpg", "eid.png", "eid.jpg"}
    attached_files = set(a["filename"].lower() for a in attachments) if attachments else set()
    has_commercial = any(f in attached_files for f in ["commercial.png", "commercial.jpg"])
    has_eid = any(f in attached_files for f in ["eid.png", "eid.jpg"])

    if attachments:
        if has_commercial and has_eid:
            # Update onboarding_step
            supabase.table("users").update({"onboarding_step": "document_verification"}).eq("email", from_email).execute()
        elif not has_commercial or not has_eid:
            missing = []
            if not has_commercial:
                missing.append("commercial.png or commercial.jpg")
            if not has_eid:
                missing.append("eid.png or eid.jpg")
            subject = "Missing Document(s) for Onboarding"
            body = f"Please attach the following missing document(s): {', '.join(missing)}"
            send_email(to_email=from_email, subject=subject, body=body)
            print(f"[INFO] Requested missing docs from: {from_email}")
            return

    # ✅ Step 2: Log user message in conversation
    supabase.table("conversations").insert({
        "user_email": from_email,
        "role": "user",
        "message": body,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

    # ✅ Step 3: Search FAQ for context
    top_chunks = retrieve_similar_chunks(body, top_k=3)
    faq_context = "\n\n".join(top_chunks)

    # ✅ Step 3.1: Get conversation history for context
    convo_response = supabase.table("conversations").select("*").eq("user_email", from_email).order("timestamp").execute()
    convo_history = convo_response.data if convo_response.data else []
    convo_context = "\n".join([f"{msg['role']}: {msg['message']}" for msg in convo_history])

    # ✅ Step 4: Build prompt and call LLM with both contexts
    full_context = f"{convo_context}\n\nFAQ:\n{faq_context}"
    prompt = build_onboarding_prompt(user_message=body, context=full_context)

    llm_response = call_local_llm(prompt)

    # ✅ Step 5: Send reply
    subject = "Re: Your query with Thrivv"
    send_email(to_email=from_email, subject=subject, body=llm_response)

    # ✅ Step 6: Log agent message in conversation
    supabase.table("conversations").insert({
        "user_email": from_email,
        "role": "agent",
        "message": llm_response,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

    print(f"[INFO] Replied to: {from_email}")

