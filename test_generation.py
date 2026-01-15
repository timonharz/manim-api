import requests
import json
import sys

# API Configuration
# If running locally vs remote
API_URL = "https://manim-api-xomj.onrender.com/generate"
OUTPUT_FILENAME = "generated_narration.mp4"

def generate_video(prompt):
    print(f"Sending prompt to {API_URL}: '{prompt}'")
    
    payload = {
        "prompt": prompt,
        "quality": "low",
        "format": "mp4"
    }

    try:
        response = requests.post(API_URL, json=payload, stream=True, timeout=120) # 2 min timeout for generation
        
        if response.status_code == 200:
            print("Generation successful! Downloading video...")
            with open(OUTPUT_FILENAME, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Video saved to {OUTPUT_FILENAME}")
        else:
            print(f"Error {response.status_code}:")
            try:
                print(response.json())
            except:
                print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    prompt = "Explain the concept of a circle radius using a red circle and an arrow."
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    generate_video(prompt)
