# backend/llm_runner/run_model.py
import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "meta-llama-3.1-8b-instruct-q6_k"

def call_local_llm(prompt: str) -> str:
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"
