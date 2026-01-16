import requests
import json
import argparse
import sys
import unittest
import os
from typing import Dict, Any

# API Configuration
BASE_URL = "https://manim-api-production.up.railway.app"

# Sample Manim Code for Testing Rendering
VALID_CODE = """
from manimlib import *
class TestScene(Scene):
    def construct(self):
        circle = Circle().set_fill(BLUE, opacity=0.5)
        self.play(ShowCreation(circle))
        self.wait()
"""

INVALID_CODE = """
from manimlib import *
class BrokenScene(Scene):
    def construct(self):
        # Missing parenthesis
        circle = Circle(
"""

class ManimAPITestSuite(unittest.TestCase):
    """
    Capability-based test suite for the Manim API.
    """
    
    @classmethod
    def setUpClass(cls):
        cls.api_key = os.getenv("GROQ_API_KEY")
        if not cls.api_key:
            print("Warning: GROQ_API_KEY not set in environment. Some tests will be skipped or fail.")

    def test_01_health_check(self):
        """Capability: Server is online and responsive."""
        print("\nChecking server health...")
        response = requests.get(f"{BASE_URL}/", timeout=None)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Manim Video Streaming API", data.get("name", ""))
        print("OK: Server is healthy.")

    def test_02_render_capability(self):
        """Capability: Render valid Manim code to MP4."""
        print("Checking rendering capability...")
        payload = {
            "code": VALID_CODE,
            "quality": "low",
            "format": "mp4"
        }
        response = requests.post(f"{BASE_URL}/render", json=payload, timeout=None)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Type"), "video/mp4")
        self.assertTrue(len(response.content) > 0)
        with open("test_render_output.mp4", "wb") as f:
            f.write(response.content)
        print("OK: Rendering works. Saved to test_render_output.mp4")

    def test_03_generate_capability(self):
        """Capability: Generate video from prompt with AI."""
        if not self.api_key:
            self.skipTest("GROQ_API_KEY not provided.")
            
        print(f"Checking AI generation capability...")
        payload = {
            "prompt": "Explain Pythagoras theorem with a triangle",
            "quality": "low",
            "format": "mp4",
            "api_key": self.api_key
        }
        # Explicitly removed timeout for generation
        response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=None)
        self.assertEqual(response.status_code, 200, f"Generate failed: {response.text}")
        self.assertEqual(response.headers.get("Content-Type"), "video/mp4")
        self.assertTrue(len(response.content) > 0)
        with open("test_generate_output.mp4", "wb") as f:
            f.write(response.content)
        print("OK: AI Generation works. Saved to test_generate_output.mp4")

    def test_04_invalid_api_key_handling(self):
        """Capability: Handle invalid API keys gracefully."""
        print("Checking error handling for invalid API key...")
        payload = {
            "prompt": "Irrelevant",
            "api_key": "gsk_invalid_key_for_testing"
        }
        response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=None)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Generation failed", response.json().get("detail", ""))
        print("OK: Invalid API key handled (returned 400).")

    def test_05_validation_error_handling(self):
        """Capability: Validate request body (Pydantic)."""
        print("Checking validation error handling...")
        payload = {
            # "prompt" is missing
            "quality": "low"
        }
        response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=None)
        self.assertEqual(response.status_code, 422)
        print("OK: Missing fields handled (returned 422).")

def run_tests(api_key=None):
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
    
    suite = unittest.TestLoader().loadTestsFromTestCase(ManimAPITestSuite)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manim API Test Client & Capability Suite")
    parser.add_argument("--api-key", help="Groq API Key for /generate tests")
    parser.add_argument("--run-all", action="store_true", help="Run the capability test suite")
    
    # Keep legacy CLI support if needed, but the user wants a unit test
    args = parser.parse_args()
    
    if args.run_all or (not len(sys.argv) > 1):
        run_tests(args.api_key)
    else:
        # If the user wants to run specific manual tests, they can still do so
        # but the primary focus is now the suite.
        print("Note: Running manual tests. Use --run-all for the full capability suite.")
        # ... logic for manual tests if needed, or just run the suite by default.
        run_tests(args.api_key)

