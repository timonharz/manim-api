import os
from typing import Tuple
from groq import Groq
from dotenv import load_dotenv

from manim_knowledge_base import retrieve_relevant_knowledge

load_dotenv()


class LLMService:
    """
    LLM Service with RAG-based manimlib knowledge retrieval.
    
    Uses keyword matching to retrieve relevant manimlib documentation
    and injects it into the system prompt for better code generation.
    """
    
    def __init__(self):
        self.default_api_key = os.getenv("GROQ_API_KEY")

    def _call_llm(self, messages: list, api_key: str) -> str:
        """Helper to call the Groq API."""
        client = Groq(api_key=api_key)
        print(f"DEBUG: Calling LLM with system prompt: {messages[0]['content'][:50]}...")
        completion = client.chat.completions.create(
            messages=messages,
            model="openai/gpt-oss-120b",
            temperature=0.7,
            max_completion_tokens=4096 
        )
        return completion.choices[0].message.content

    def generate_storyboard(self, prompt: str, knowledge: str, api_key: str) -> str:
        """Step 1: Generate a visual storyboard."""
        system_prompt = f"""You are an expert director for educational math videos. Create a detailed storyboard.
        
## RELEVANT KNOWLEDGE:
{knowledge}

## OUTPUT FORMAT:
[STORYBOARD]
1. [0:00-0:10] Intro: ... (Visuals: ...)
2. [0:10-0:30] Concept: ... (Visuals: ...)
...
[/STORYBOARD]
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a storyboard for: {prompt}"}
        ]
        return self._call_llm(messages, api_key)

    def generate_script(self, storyboard: str, api_key: str) -> str:
        """Step 2: Generate narration script from storyboard."""
        system_prompt = """You are an expert science communicator. Write a narration script matching the storyboard.
        
## OUTPUT FORMAT:
[SCRIPT]
(Write the full narration here. Use "..." for pauses. Be engaging and clear.)
[/SCRIPT]
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Write a script for this storyboard:\n{storyboard}"}
        ]
        return self._call_llm(messages, api_key)

    def generate_code(self, prompt: str, storyboard: str, script: str, knowledge: str, api_key: str) -> str:
        """Step 3: Generate Manim code from storyboard and script."""
        system_prompt = f"""You are an expert Manim animation developer. Generate Python code using `manimlib` (ManimGL).

## CONTEXT:
STORYBOARD:
{storyboard}

SCRIPT:
{script}

## RELEVANT DOCUMENTATION:
{knowledge}

## OUTPUT FORMAT:
[CODE]
(Python code only)
[/CODE]

## CRITICAL RULES (VIOLATION = SYSTEM CRASH):
1. Use ONLY `from manimlib import *` as the FIRST import line.
2. NEVER use `import manim` or `from manim import ...`.
3. Include `self.add_sound("narration.mp3")` at the start of `construct`.
4. Use `self.wait()` to sync with the script timing.
5. PREFER `Text("String")` over `Tex(r"\\text{{String}}")`.
6. Use `self.frame.set_euler_angles()` for 3D camera.
7. Use `ShowCreation` (not Create), `Tex` (not MathTex).
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate Manim code for: {prompt}"}
        ]
        client = Groq(api_key=api_key)
        # Use larger token limit for code
        completion = client.chat.completions.create(
            messages=messages,
            model="openai/gpt-oss-120b",
            temperature=0.7,
            max_completion_tokens=16384
        )
        return completion.choices[0].message.content

    def generate_manim_content(self, prompt: str, api_key: str) -> Tuple[str, str]:
        """
        Orchestrates the 3-step generation pipeline.
        """
        if not api_key:
            raise ValueError("Groq API key is required.")

        # 0. Retrieve Knowledge
        knowledge = retrieve_relevant_knowledge(prompt, max_sections=6)

        # 1. Storyboard
        print("DEBUG: Generating Storyboard...")
        storyboard_resp = self.generate_storyboard(prompt, knowledge, api_key)
        print(f"DEBUG: Storyboard generated (len={len(storyboard_resp)})")

        # 2. Script
        print("DEBUG: Generating Script...")
        script_resp = self.generate_script(storyboard_resp, api_key)
        
        # Extract script content
        import re
        script_match = re.search(r"\[\s*SCRIPT\s*\](.*?)\[\s*/SCRIPT\s*\]", script_resp, re.DOTALL | re.IGNORECASE)
        script = script_match.group(1).strip() if script_match else script_resp
        print(f"DEBUG: Script generated (len={len(script)})")

        # 3. Code
        print("DEBUG: Generating Code...")
        # RE-RETRIEVE knowledge using the Storyboard to catch technical keywords (e.g. "graph", "3d")
        # that might have been in the generated plan but not the initial simple prompt.
        code_knowledge = retrieve_relevant_knowledge(storyboard_resp + "\n" + prompt, max_sections=8)
        print(f"DEBUG: Retrieved code context: {len(code_knowledge)} chars")
        
        code_resp = self.generate_code(prompt, storyboard_resp, script, code_knowledge, api_key)
        
        # Extract code content
        code_match = re.search(r"\[\s*CODE\s*\](.*?)\[\s*/CODE\s*\]", code_resp, re.DOTALL | re.IGNORECASE)
        if not code_match:
             code_match = re.search(r"```python(.*?)```", code_resp, re.DOTALL)
        
        code = code_match.group(1).strip() if code_match else code_resp
        
        # --- POST PROCESSING & SANITIZATION ---
        
        # Clean up code block markers
        if code.startswith("```"):
            code = code.strip("`").strip()
            if code.startswith("python"): code = code[6:].strip()

        # Fix imports
        if "from manimlib import" not in code:
            code = "from manimlib import *\n\n" + code

        # Fix always_redraw
        always_redraw_pattern = re.compile(r'(\w+)\s*=\s*always_redraw\s*\(\s*(\w+)\s*\)')
        if always_redraw_pattern.search(code):
             def fix_always_redraw(match):
                var_name = match.group(1)
                func_name = match.group(2)
                return f'{var_name} = {func_name}()\n        {var_name}.add_updater(lambda m: m.become({func_name}()))'
             code = always_redraw_pattern.sub(fix_always_redraw, code)

        # Fix common hallucinations
        code = re.sub(r'\bMathTex\b', 'Tex', code)
        code = re.sub(r'\bCreate\b(?!\w)', 'ShowCreation', code)
        
        # Fix Unicode
        code = code.replace('–', '-').replace('—', '-')
        
        # Final Sanitization: \text{...} -> \mathrm{...}
        if r"\text{" in code:
            print("DEBUG: Sanitizing LaTeX \\text{ usages...")
            code = re.sub(r'\\text\{([^}]+)\}', r'\\mathrm{\1}', code)

        print(f"DEBUG: Code generated (len={len(code)})")
        return code.strip(), script

