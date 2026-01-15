import requests
import json
import argparse
import sys

# API Configuration
BASE_URL = "https://manim-api-xomj.onrender.com"

# Sample Manim Code
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

def test_render(output_filename="test_render.mp4"):
    url = f"{BASE_URL}/render"
    print(f"Testing /render endpoint at {url}...")
    
    payload = {
        "code": CODE,
        "quality": "low",
        "format": "mp4"
    }

    send_request(url, payload, output_filename)

def test_generate(prompt, output_filename="test_generated.mp4", api_key=None):
    url = f"{BASE_URL}/generate"
    print(f"Testing /generate endpoint at {url} with prompt: '{prompt}'...")
    
    payload = {
        "prompt": prompt,
        "quality": "low",
        "format": "mp4"
    }
    
    if api_key:
        payload["api_key"] = api_key
    else:
        # Try to find key in env vars
        import os
        key = os.getenv("GROQ_API_KEY")
        if key:
            print("Using GROQ_API_KEY from environment.")
            payload["api_key"] = key
        else:
            print("Warning: No API key provided and GROQ_API_KEY not set.")

    send_request(url, payload, output_filename)

def send_request(url, payload, output_filename):
    try:
        response = requests.post(url, json=payload, stream=True, timeout=120)
        
        if response.status_code == 200:
            print("Request successful! Downloading video...")
            with open(output_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Video saved to {output_filename}")
        else:
            print(f"Error {response.status_code}:")
            try:
                print(response.json())
            except:
                print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Manim API endpoints")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Render command
    render_parser = subparsers.add_parser("render", help="Test /render endpoint with sample code")
    render_parser.add_argument("-o", "--output", default="test_render.mp4", help="Output filename")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Test /generate endpoint with prompt")
    gen_parser.add_argument("prompt", help="Text prompt for video generation")
    gen_parser.add_argument("-o", "--output", default="test_generated.mp4", help="Output filename")
    gen_parser.add_argument("--api-key", help="Groq API Key")
    
    args = parser.parse_args()
    
    if args.command == "render":
        test_render(args.output)
    elif args.command == "generate":
        test_generate(args.prompt, args.output, args.api_key)
    else:
        # Default behavior for backward compatibility or ease of use
        print("No command specified. Usage:")
        print("  python test_client.py render")
        print("  python test_client.py generate \"Your prompt here\"")
        print("\nRunning default render test...")
        test_render()
