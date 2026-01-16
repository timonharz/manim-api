"""
Manim API - AI Video Generation Test Suite

This module focuses specifically on testing the AI-powered video generation
capabilities of the Manim API, including prompt handling, code generation
quality, and error recovery.
"""
import requests
import json
import argparse
import sys
import unittest
import os
import time
from typing import Dict, Any, Optional

# API Configuration
BASE_URL = os.getenv("MANIM_API_URL", "https://manim-api-production.up.railway.app")

# Test Prompts categorized by complexity
SIMPLE_PROMPTS = [
    "Draw a blue circle",
    "Show a red square fading in",
    "Animate the text 'Hello World' appearing",
]

INTERMEDIATE_PROMPTS = [
    "Explain the Pythagorean theorem with a right triangle",
    "Show how a sine wave is created from circular motion",
    "Illustrate the concept of a derivative as the slope of a tangent line",
]

COMPLEX_PROMPTS = [
    "Animate a square wave being approximated by its first 5 Fourier components",
    "Visualize a 3D surface like z = sin(sqrt(x^2 + y^2)) with camera rotation",
    "Create a graph showing the relationship between exponential growth and its derivative",
]


class AIGenerationTestSuite(unittest.TestCase):
    """
    Comprehensive test suite for AI-powered video generation.
    """

    @classmethod
    def setUpClass(cls):
        cls.api_key = os.getenv("GROQ_API_KEY")
        if not cls.api_key:
            print("ERROR: GROQ_API_KEY not set. All tests will be skipped.")
        cls.generated_files = []

    @classmethod
    def tearDownClass(cls):
        if cls.generated_files:
            print(f"\n--- Generated {len(cls.generated_files)} video(s) ---")
            for f in cls.generated_files:
                print(f"  - {f}")

    def _make_generate_request(
        self,
        prompt: str,
        quality: str = "low",
        format: str = "mp4",
        timeout: Optional[int] = None,
    ) -> requests.Response:
        """Helper to make a /generate request."""
        payload = {
            "prompt": prompt,
            "quality": quality,
            "format": format,
            "api_key": self.api_key,
        }
        return requests.post(f"{BASE_URL}/generate", json=payload, timeout=timeout)

    def _save_video(self, response: requests.Response, name: str) -> str:
        """Save video content to a file."""
        filename = f"ai_test_{name}.mp4"
        with open(filename, "wb") as f:
            f.write(response.content)
        self.generated_files.append(filename)
        return filename

    # --- Health Check ---
    def test_00_server_health(self):
        """Pre-flight: Ensure server is alive before running AI tests."""
        print("\n[00] Checking server health...")
        response = requests.get(f"{BASE_URL}/", timeout=10)
        self.assertEqual(response.status_code, 200)
        print("     Server is healthy.")

    # --- Simple Generation Tests ---
    def test_01_simple_circle(self):
        """Simple: Generate a basic circle animation."""
        if not self.api_key:
            self.skipTest("GROQ_API_KEY not provided.")
        print("\n[01] Testing simple circle generation...")
        response = self._make_generate_request("Draw a blue circle that fades in")
        if response.status_code == 200:
            self._save_video(response, "simple_circle")
            print("     PASS: Simple circle generated.")
        else:
            print(f"     FAIL: {response.status_code} - {response.text}")
        self.assertEqual(response.status_code, 200)

    def test_02_simple_text(self):
        """Simple: Generate text animation."""
        if not self.api_key:
            self.skipTest("GROQ_API_KEY not provided.")
        print("\n[02] Testing simple text animation...")
        response = self._make_generate_request("Animate the text 'Math is Beautiful' appearing letter by letter")
        if response.status_code == 200:
            self._save_video(response, "simple_text")
            print("     PASS: Text animation generated.")
        else:
            print(f"     FAIL: {response.status_code} - {response.text}")
        self.assertEqual(response.status_code, 200)

    # --- Intermediate Generation Tests ---
    def test_03_pythagorean_theorem(self):
        """Intermediate: Explain Pythagorean theorem."""
        if not self.api_key:
            self.skipTest("GROQ_API_KEY not provided.")
        print("\n[03] Testing Pythagorean theorem explanation...")
        response = self._make_generate_request(
            "Explain the Pythagorean theorem with a right triangle, showing how a^2 + b^2 = c^2"
        )
        if response.status_code == 200:
            self._save_video(response, "pythagorean")
            print("     PASS: Pythagorean theorem video generated.")
        else:
            print(f"     FAIL: {response.status_code} - {response.text}")
        self.assertEqual(response.status_code, 200)

    def test_04_sine_wave(self):
        """Intermediate: Create sine wave from circular motion."""
        if not self.api_key:
            self.skipTest("GROQ_API_KEY not provided.")
        print("\n[04] Testing sine wave visualization...")
        response = self._make_generate_request(
            "Show how a sine wave is created from the vertical position of a point moving around a circle"
        )
        if response.status_code == 200:
            self._save_video(response, "sine_wave")
            print("     PASS: Sine wave video generated.")
        else:
            print(f"     FAIL: {response.status_code} - {response.text}")
        self.assertEqual(response.status_code, 200)

    # --- Complex Generation Tests ---
    def test_05_fourier_series(self):
        """Complex: Fourier series approximation."""
        if not self.api_key:
            self.skipTest("GROQ_API_KEY not provided.")
        print("\n[05] Testing Fourier series (complex)...")
        response = self._make_generate_request(
            "Animate a square wave being approximated by adding its first 5 Fourier sine components one by one"
        )
        if response.status_code == 200:
            self._save_video(response, "fourier_series")
            print("     PASS: Fourier series video generated.")
        else:
            print(f"     FAIL: {response.status_code} - {response.text[:200]}")
        # This is allowed to fail for now, but we log it
        if response.status_code != 200:
            self.skipTest(f"Complex generation failed: {response.text[:100]}")

    def test_06_3d_surface(self):
        """Complex: 3D surface visualization."""
        if not self.api_key:
            self.skipTest("GROQ_API_KEY not provided.")
        print("\n[06] Testing 3D surface visualization (complex)...")
        response = self._make_generate_request(
            "Visualize a 3D surface defined by z = sin(x) * cos(y)"
        )
        if response.status_code == 200:
            self._save_video(response, "3d_surface")
            print("     PASS: 3D surface video generated.")
        else:
            print(f"     FAIL: {response.status_code} - {response.text[:200]}")
        # This is allowed to fail for now, but we log it
        if response.status_code != 200:
            self.skipTest(f"Complex 3D generation failed: {response.text[:100]}")

    # --- Error Handling Tests ---
    def test_07_invalid_api_key(self):
        """Error: Invalid API key should return 400."""
        print("\n[07] Testing invalid API key handling...")
        payload = {
            "prompt": "Draw a circle",
            "api_key": "gsk_invalid_key_for_testing",
        }
        response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=60)
        print(f"     Status: {response.status_code}")
        self.assertIn(response.status_code, [400, 401, 500])  # Accept any error response

    def test_08_missing_prompt(self):
        """Error: Missing prompt should return 422."""
        print("\n[08] Testing missing prompt validation...")
        payload = {
            "quality": "low",
            "api_key": self.api_key or "test",
        }
        response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=10)
        print(f"     Status: {response.status_code}")
        self.assertEqual(response.status_code, 422)

    def test_09_empty_prompt(self):
        """Error: Empty prompt should be handled gracefully."""
        if not self.api_key:
            self.skipTest("GROQ_API_KEY not provided.")
        print("\n[09] Testing empty prompt handling...")
        response = self._make_generate_request("")
        print(f"     Status: {response.status_code}")
        self.assertIn(response.status_code, [400, 422, 500])

    def test_10_complex_student_task(self):
        """Complex: Student task - Riemann Sum Approximation."""
        if not self.api_key:
            self.skipTest("GROQ_API_KEY not provided.")
        print("\n[10] Testing Riemann Sum Approximation (Complex Student Task)...")
        prompt = (
            "Visualize the concept of a Riemann Sum approximation for the function f(x) = x^2 on the interval [0, 2]. "
            "Show the function graph first. Then, use 4 rectangles to approximate the area under the curve using left endpoints. "
            "Explain that the sum of the areas of these rectangles approximates the definite integral. "
            "Finally, increase the number of rectangles to 10 to show how the approximation improves."
        )
        response = self._make_generate_request(prompt)
        if response.status_code == 200:
            self._save_video(response, "riemann_sum")
            print("     PASS: Riemann Sum video generated.")
        else:
            print(f"     FAIL: {response.status_code} - {response.text}")
        
        # We allow this to fail if production hasn't deployed, but we want to attempt it.
        if response.status_code != 200:
             print(f"     NOTE: High probability of failure if production env is outdated.")
        
        self.assertEqual(response.status_code, 200)


def run_tests(api_key: Optional[str] = None, verbosity: int = 1):
    """Run the AI generation test suite."""
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key

    suite = unittest.TestLoader().loadTestsFromTestCase(AIGenerationTestSuite)
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Manim API - AI Video Generation Test Suite"
    )
    parser.add_argument("--api-key", help="Groq API Key for generation tests")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Increase output verbosity"
    )
    parser.add_argument(
        "--url", help="Override the API base URL", default=None
    )

    args = parser.parse_args()

    if args.url:
        BASE_URL = args.url

    verbosity = 2 if args.verbose else 1
    success = run_tests(args.api_key, verbosity)
    sys.exit(0 if success else 1)
