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
3. Create a SINGLE `Scene` class named `GeneratedScene` containing the ENTIRE animation.
4. DO NOT create multiple Scene classes. Combine all storyboard parts into one `construct` method.
5. Include `self.add_sound("narration.mp3")` at the start of `construct`.
6. Use `self.wait()` to sync with the script timing.
7. PREFER `Text("String")` over `Tex(r"\\text{{String}}")`.
8. Use `self.frame.set_euler_angles()` for 3D camera.
9. Use `ShowCreation` (not Create), `Tex` (not MathTex).
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

    def _extract_code(self, response: str) -> str:
        """Extracts and dedents code from LLM response."""
        import re
        import textwrap
        
        code = None
        
        # 1. Try explicit [CODE] tags
        match = re.search(r"\[\s*CODE\s*\](.*?)\[\s*/CODE\s*\]", response, re.DOTALL | re.IGNORECASE)
        if match:
            code = match.group(1)
            
        # 2. Try Markdown code blocks
        if not code:
            match = re.search(r"```python(.*?)```", response, re.DOTALL | re.IGNORECASE)
            if match:
                code = match.group(1)

        # 3. Fallback: Heuristic extraction
        if not code:
            # Look for common starting points
            start_patterns = ["from manimlib import", "import manimlib", "class "]
            start_idx = -1
            for p in start_patterns:
                idx = response.find(p)
                if idx != -1:
                    if start_idx == -1 or idx < start_idx:
                        start_idx = idx
            
            if start_idx != -1:
                code = response[start_idx:]
                # Basic cleanup of trailing markdown
                if "```" in code:
                    code = code.split("```")[0]
            else:
                code = response  # Absolute desperation
        
        # Critical: Dedent the code
        if code:
            # First, strip empty lines from start/end
            code = code.strip()
            # Then dedent - this handles cases where the LLM indented the whole block
            return textwrap.dedent(code)
            
        return ""

    def _post_process_code(self, code: str) -> str:
        """Sanitizes and fixes common issues in generated code."""
        import re
        
        # 1. Fix Imports
        if "from manimlib import" not in code:
            code = "from manimlib import *\n\n" + code
            
        # 2. Fix always_redraw
        always_redraw_pattern = re.compile(r'(\w+)\s*=\s*always_redraw\s*\(\s*(\w+)\s*\)')
        if always_redraw_pattern.search(code):
             def fix_always_redraw(match):
                var_name = match.group(1)
                func_name = match.group(2)
                return f'{var_name} = {func_name}()\n        {var_name}.add_updater(lambda m: m.become({func_name}()))'
             code = always_redraw_pattern.sub(fix_always_redraw, code)

        # 3. Fix common hallucinations
        code = re.sub(r'\bMathTex\b', 'Tex', code)
        code = re.sub(r'\bCreate\b(?!\w)', 'ShowCreation', code)
        
        # 4. Fix Unicode
        code = code.replace('–', '-').replace('—', '-')
        
        # 5. LaTeX Sanitization
        if r"\text{" in code:
            code = re.sub(r'\\text\{([^}]+)\}', r'\\mathrm{\1}', code)
            
        # 6. Ensure Class Structure (Wrap naked fragments)
        import re
        if not re.search(r"class\s+\w+\(Scene\):", code):
            # No scene class found, wrap it
            indented_code = "\n".join(["    " + line for line in code.split("\n")])
            code = f"""
from manimlib import *

class GeneratedScene(Scene):
    def construct(self):
{indented_code}
"""
        
        return code

    def generate_manim_content(self, prompt: str, api_key: str) -> Tuple[str, str]:
        """
        Orchestrates the 3-step generation pipeline.
        """
        if not api_key:
            api_key = self.default_api_key
            
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
        # RE-RETRIEVE knowledge using the Storyboard
        code_knowledge = retrieve_relevant_knowledge(storyboard_resp + "\n" + prompt, max_sections=8)
        print(f"DEBUG: Retrieved code context: {len(code_knowledge)} chars")
        
        code_resp = self.generate_code(prompt, storyboard_resp, script, code_knowledge, api_key)
        print(f"DEBUG: Raw LLM Code Response (first 500 chars):\n{code_resp[:500]}...")
        
        # --- Extraction & Processing ---
        code = self._extract_code(code_resp)
        code = self._post_process_code(code)
        
        print(f"DEBUG: Code generated (len={len(code)})")
        
        # --- Final Validation ---
        import ast
        try:
            ast.parse(code)
            print("DEBUG: Generated code passed AST syntax check.")
        except SyntaxError as e:
            print(f"DEBUG: Generated code FAILED AST check: {e}")
            # We don't raise here, we attempt to return what we have, 
            # maybe the user can debug it or the renderer catches it with a better error.
            # But logging it is crucial.
            
        return code.strip(), script

