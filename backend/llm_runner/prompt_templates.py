# backend/llm_runner/prompt_templates.py

def build_onboarding_prompt(user_message: str, context: str = "") -> str:
    # Extract onboarding_step from context
    onboarding_step = "welcome"
    if context.startswith("Onboarding Step:"):
        onboarding_step = context.split("\n")[0].split(":")[1].strip()

    if onboarding_step == "welcome":
        instructions = (
            "Ask the user these questions one by one, waiting for their answer before moving to the next:\n"
            "1) What kind of account would you like to open—Savings or Commercial?\n"
            "2) Do you confirm that you are over 18 years of age? If yes, proceed. Otherwise, inform them they are not eligible.\n"
            "3) What is your gross yearly salary? (Just remember the salary.)\n"
            "4) Please submit the following documents as image files: Emirates ID (EID) and Commercial License."
        )
    elif onboarding_step == "document_verification":
        instructions = (
            "Inform the user that all relevant documents have been received and are being verified. Ask if they have any other queries."
        )
    elif onboarding_step == "verification_complete":
        instructions = (
            "Congratulate the user for being onboarded and inform them that account details will be shared within 3-4 business days."
        )
    else:
        instructions = "Respond helpfully to the user's query."

    prompt = f"""
You are an intelligent and friendly onboarding assistant at Thrivv.

Current onboarding step: {onboarding_step}
Instructions: {instructions}

Here is a question from the user:
\"\"\"{user_message}\"\"\"

Relevant background information:
\"\"\"{context}\"\"\"

Please respond in a helpful, conversational tone.
"""
    return prompt.strip()
