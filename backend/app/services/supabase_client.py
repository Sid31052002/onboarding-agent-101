# app/services/supabase_client.py
# app/services/supabase_client.py

from datetime import date  # ✅ Add this
from app.config import SUPABASE_URL, SUPABASE_API_KEY
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_API_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

def insert_user(user_data: dict) -> dict:
    try:
        # Convert date objects to ISO strings
        for key, value in user_data.items():
            if isinstance(value, date):
                user_data[key] = value.isoformat()

        response = supabase.table("users").insert(user_data).execute()
        return response.data[0]

    except Exception as e:
        raise Exception(f"Supabase insert failed: {str(e)}")


def get_user_by_email(email: str) -> dict | None:
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        raise Exception(f"Supabase select failed: {str(e)}")

# app/services/supabase_client.py

def insert_conversation_log(log: dict) -> dict:
    try:
        log["timestamp"] = log["timestamp"].isoformat()  # Serialize datetime
        response = supabase.table("conversations").insert(log).execute()
        return response.data[0]
    except Exception as e:
        raise Exception(f"Supabase insert conversation failed: {str(e)}")

