import requests
import json

# API Configuration
API_URL = "https://manim-api-xomj.onrender.com/render"
OUTPUT_FILENAME = "test_animation.mp4"

# Sample Manim Code
# A simple scene with a circle and some text
CODE = """
from manimlib import *

class TestScene(Scene):
    def construct(self):
        circle = Circle()
        circle.set_fill(BLUE, opacity=0.5)
        
        text = Text("Hello Render!", font_size=40)
        text.next_to(circle, UP)
        
        self.play(ShowCreation(circle))
        self.play(Write(text))
        self.wait()
"""

def generate_video():
    print(f"Sending request to {API_URL}...")
    
    payload = {
        "code": CODE,
        "quality": "low", # Use low quality for faster testing
        "format": "mp4"
    }

    try:
        response = requests.post(API_URL, json=payload, stream=True)
        
        if response.status_code == 200:
            print("Render successful! Downloading video...")
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
    generate_video()
