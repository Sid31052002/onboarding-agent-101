import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")

BASE_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}"
HEADERS = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json"
}

if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
    raise ValueError("RUNPOD_API_KEY or RUNPOD_ENDPOINT_ID missing. Check .env file.")

# 🔹 Simple test prompt
test_prompt = """
Customer question: "How do I reset my online banking password?"

FAQ:
- Go to the login page and click 'Forgot Password'.
- You’ll receive a reset link via email.
- Follow the link to set a new password.
"""

# 🔹 Payload for RunPod
data = {
    "input": {
        "prompt": test_prompt,
        "max_tokens": 100,
        "temperature": 0.2
    }
}

print("Submitting test job...")
response = requests.post(f"{BASE_URL}/run", headers=HEADERS, json=data)
job = response.json()
print("Job submitted:", job)

job_id = job.get("id")
if not job_id:
    raise RuntimeError("No job ID returned from RunPod!")

# 🔹 Poll until completed
print("\nPolling for result...")
for _ in range(20):  # max 20 polls
    status_response = requests.get(f"{BASE_URL}/status/{job_id}", headers=HEADERS)
    status_json = status_response.json()
    print("Status:", status_json.get("status"))

    if status_json.get("status") == "COMPLETED":
        print("\n=== Job Output ===")
        print(status_json.get("output"))
        break
    elif status_json.get("status") == "FAILED":
        print("\nJob failed:", status_json)
        break

    time.sleep(3)  # wait before polling again
+.320