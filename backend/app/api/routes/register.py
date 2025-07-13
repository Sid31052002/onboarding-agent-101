# app/api/routes/register.py

from fastapi import APIRouter, HTTPException
from app.models.user import UserRegisterRequest
from app.services.supabase_client import insert_user, get_user_by_email
from app.services.email_sender import send_welcome_email
from app.services.supabase_client import insert_conversation_log
from app.models.conversation import ConversationLog
from datetime import datetime

router = APIRouter()

@router.post("/register")
def register_user(user: UserRegisterRequest):
    try:
        # Duplicate check
        if get_user_by_email(user.email):
            raise HTTPException(status_code=409, detail="Email already registered")

        user_dict = user.dict()
        inserted_user = insert_user(user_dict)

        # 1️⃣ Send Welcome Email
        send_welcome_email(user.email, user.name)

        # 2️⃣ Log Welcome Message to conversations table
        convo = ConversationLog(
            user_email=user.email,
            role="agent",
            message="Welcome to Thrivv! Please reply with 'Continue' or 'Exit'.",
            timestamp=datetime.utcnow()
        )
        insert_conversation_log(convo.dict())

        return {"message": "User registered successfully", "user": inserted_user}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
