# backend/llm_pipeline/handle_reply.py

from ingestion.faq_retriever import retrieve_similar_chunks
from llm_runner.prompt_templates import build_onboarding_prompt
from llm_runner.run_model import call_local_llm
from app.services.supabase_client import supabase
from app.services.email_sender import send_email

from datetime import datetime

def process_user_reply(from_email: str, body: str):
    # ✅ Step 1: Get the user
    user_response = supabase.table("users").select("*").eq("email", from_email).execute()
    if not user_response.data or len(user_response.data) == 0:
        print(f"[WARN] Email not found in users table: {from_email}")
        return

    user = user_response.data[0]

    # ✅ Step 2: Log user message in conversation
    supabase.table("conversations").insert({
        "user_email": from_email,
        "role": "user",
        "message": body,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

    # ✅ Step 3: Search FAQ for context
    top_chunks = retrieve_similar_chunks(body, top_k=3)
    context = "\n\n".join(top_chunks)

    # ✅ Step 4: Build prompt and call LLM
    prompt = build_onboarding_prompt(user_message=body, context=context)

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

