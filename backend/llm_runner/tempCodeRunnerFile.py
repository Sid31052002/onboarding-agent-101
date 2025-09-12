from transformers import AutoProcessor, AutoModelForVision2Seq
import torch
from PIL import Image

# Load processor and model
processor = AutoProcessor.from_pretrained("numind/NuMarkdown-8B-Thinking")
model = AutoModelForVision2Seq.from_pretrained("numind/NuMarkdown-8B-Thinking")

# Load a test image (replace with your own image path)
image = Image.open(r"F:/Freelance/onboarding-agent-101/backend/documents/id/siddharthvermaofficial3105@gmail.com\Docuemt-1.png").convert("RGB")

# Prepare inputs
inputs = processor(images=image, return_tensors="pt").to(model.device)

# Generate output
with torch.no_grad():
    generated_ids = model.generate(**inputs, max_new_tokens=256)
    output_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

print("\n=== Model Output ===")
print(output_text)
