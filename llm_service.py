import os
from typing import Tuple
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        # We can keep an optional default client if needed, or just warn.
        self.default_api_key = os.getenv("GROQ_API_KEY")

    def generate_manim_content(self, prompt: str, api_key: str = None) -> Tuple[str, str]:
        """
        Generates Manim Python code and a narration script from a text prompt.
        
        Args:
            prompt: User prompt.
            api_key: Groq API key provided by the user (override).
            
        Returns:
            (code, narration script)
        """
        key_to_use = api_key or self.default_api_key
        if not key_to_use:
            raise ValueError("Groq API key is required. Please provide it in the request or set GROQ_API_KEY env var.")
            
        client = Groq(api_key=key_to_use)

        system_prompt = """
        You are an expert Manim animation developer. Your goal is to generate Python code using `manimlib` (ManimGL version) to visualize the user's request, and a corresponding narration script.

        You must output your response in the following format exactly:
        
        [SCRIPT]
        ... (The text script for the narration, plain text)
        [/SCRIPT]
        
        [CODE]
        ... (The Python code for the scene)
        [/CODE]

        Hardware/Environment Constraints:
        - The code will be rendered in a headless environment.
        - You MUST assume an audio file named "narration.mp3" will be available in the same directory.
        - You MUST include `self.add_sound("narration.mp3")` in the `construct` method, preferably at the beginning or synced appropriately.
        - Use `manimlib` imports: `from manimlib import *`.
        - Define a single Scene class.
        """

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="openai/gpt-oss-120b",
        )

        content = completion.choices[0].message.content

        # Simple parsing logic
        try:
            script_start = content.find("[SCRIPT]") + len("[SCRIPT]")
            script_end = content.find("[/SCRIPT]")
            script = content[script_start:script_end].strip()

            code_start = content.find("[CODE]") + len("[CODE]")
            code_end = content.find("[/CODE]")
            code = content[code_start:code_end].strip()
            
            # Remove markdown code fences if present
            if code.startswith("```python"):
                code = code[9:]
            if code.startswith("```"):
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]
                
            return code.strip(), script
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}")
