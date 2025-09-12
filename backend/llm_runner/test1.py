from PIL import Image
from transformers import pipeline

ocr = pipeline("image-to-text", model="numind/NuMarkdown-8B-Thinking", trust_remote_code=True)

result = ocr(r"F:/Freelance/onboarding-agent-101/backend/documents/id/siddharthvermaofficial3105@gmail.com\Docuemt-1.png")[0]["generated_text"]
print(result)
