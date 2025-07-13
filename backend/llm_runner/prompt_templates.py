# backend/llm_runner/prompt_templates.py

def build_onboarding_prompt(user_message: str, context: str = "") -> str:
    prompt = f"""
You are an intelligent and friendly onboarding assistant at Thrivv.

Here is a question from the user:
\"\"\"{user_message}\"\"\"

Relevant background information:
\"\"\"{context}\"\"\"

Please respond in a helpful, conversational tone.
"""
    return prompt.strip()
