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
            model="llama-3.3-70b-versatile",
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
9. Use `ShowCreation` (not Create).
10. For MATH formulas (fractions, limits, integrals, etc.), use `MathTex(r"...")`. For plain TEXT, use `Text("...")` or `Tex(r"$...$")`.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate Manim code for: {prompt}"}
        ]
        client = Groq(api_key=api_key)
        # Use larger token limit for code
        completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.5,  # Lower temperature for more coherent code
            max_completion_tokens=8192
        )
        return completion.choices[0].message.content
    
    def _is_code_scrambled(self, code: str) -> bool:
        """
        Detect if code has been scrambled/interleaved by the LLM.
        Scrambled code has imports appearing in the middle, or class definitions after method bodies.
        """
        lines = code.strip().split('\n')
        
        # Check 1: 'from manimlib import' should be in the first 5 lines
        import_found_early = False
        for i, line in enumerate(lines[:5]):
            if 'from manimlib import' in line or 'import manimlib' in line:
                import_found_early = True
                break
        
        # Check if import appears LATER than line 5 (indicates scrambling)
        for i, line in enumerate(lines[5:], start=5):
            if 'from manimlib import' in line:
                print(f"DEBUG: Scrambled code detected - import on line {i+1}")
                return True
        
        # Check 2: class definition should come before method code
        class_line = -1
        first_self_line = -1
        for i, line in enumerate(lines):
            if 'class ' in line and 'Scene' in line:
                class_line = i
            if 'self.' in line and first_self_line == -1:
                first_self_line = i
        
        if first_self_line != -1 and class_line != -1 and first_self_line < class_line:
            print(f"DEBUG: Scrambled code detected - self. on line {first_self_line+1} before class on line {class_line+1}")
            return True
        
        return False

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
        # NOTE: Do NOT replace MathTex with Tex - they serve different purposes!
        # MathTex is for math mode (\frac, \lim, etc.), Tex is for text mode
        code = re.sub(r'\bCreate\b(?!\w)', 'ShowCreation', code)
        
        # 4. Fix Unicode
        code = code.replace('–', '-').replace('—', '-')
        
        # 5. Fix undefined color constants
        color_fixes = {
            'LIGHT_GRAY': 'GREY_B',
            'LIGHT_GREY': 'GREY_B', 
            'DARK_GRAY': 'GREY_D',
            'DARK_GREY': 'GREY_D',
            'LIGHT_BROWN': 'GOLD_E',
            'DARK_BROWN': 'GOLD_E',
            'LIGHT_PINK': 'PINK',
            'DARK_PINK': 'MAROON_C',
            'LIGHT_BLUE': 'BLUE_B',
            'DARK_BLUE': 'BLUE_E',
            'LIGHT_GREEN': 'GREEN_B',
            'DARK_GREEN': 'GREEN_E',
            'LIGHT_RED': 'RED_B',
            'DARK_RED': 'RED_E',
            'LIGHT_YELLOW': 'YELLOW_B',
            'DARK_YELLOW': 'YELLOW_E',
            'LIGHT_PURPLE': 'PURPLE_B',
            'DARK_PURPLE': 'PURPLE_E',
            'LIGHT_ORANGE': 'ORANGE',
            'DARK_ORANGE': 'GOLD_E',
            'CYAN': 'TEAL',
            'MAGENTA': 'PINK',
        }
        for wrong_color, correct_color in color_fixes.items():
            code = re.sub(rf'\b{wrong_color}\b', correct_color, code)
        
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
        Orchestrates the 3-step generation pipeline with validation and retry.
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
        import ast
        script_match = re.search(r"\[\s*SCRIPT\s*\](.*?)\[\s*/SCRIPT\s*\]", script_resp, re.DOTALL | re.IGNORECASE)
        script = script_match.group(1).strip() if script_match else script_resp
        print(f"DEBUG: Script generated (len={len(script)})")

        # 3. Code Generation with Retry Loop
        print("DEBUG: Generating Code...")
        # RE-RETRIEVE knowledge using the Storyboard
        code_knowledge = retrieve_relevant_knowledge(storyboard_resp + "\n" + prompt, max_sections=8)
        print(f"DEBUG: Retrieved code context: {len(code_knowledge)} chars")
        
        max_code_attempts = 3
        last_code_error = None
        code = None
        
        for attempt in range(max_code_attempts):
            try:
                # Build the effective prompt for this attempt
                effective_prompt = prompt
                if attempt > 0 and last_code_error:
                    print(f"DEBUG: Code attempt {attempt + 1}/{max_code_attempts} - retrying due to: {last_code_error}")
                    effective_prompt = f"""CRITICAL: Your previous code generation was CORRUPTED and INVALID.

ERROR: {last_code_error}

You MUST generate VALID Python code that compiles without errors.
Fix the syntax issues and generate working code.

Original request: {prompt}"""
                
                code_resp = self.generate_code(effective_prompt, storyboard_resp, script, code_knowledge, api_key)
                print(f"DEBUG: Raw LLM Code Response (first 500 chars):\n{code_resp[:500]}...")
                
                # --- Extraction & Processing ---
                code = self._extract_code(code_resp)
                code = self._post_process_code(code)
                
                print(f"DEBUG: Code generated (len={len(code)})")
                
                # --- Validation ---
                # Check for scrambled/interleaved code (LLM corruption)
                if self._is_code_scrambled(code):
                    raise ValueError("Code appears to be scrambled/interleaved - LLM produced corrupted output")
                
                # Check for illegal imports
                illegal_imports = ['from manim import', 'import manim', 'from manif', 'import manif']
                for bad_import in illegal_imports:
                    if bad_import in code:
                        raise ValueError(f"Code contains illegal import '{bad_import}'. Must use 'from manimlib import *'")
                
                # AST syntax check
                ast.parse(code)
                print(f"DEBUG: Code passed AST validation on attempt {attempt + 1}")
                
                # Success - break out of retry loop
                break
                
            except (SyntaxError, ValueError) as e:
                last_code_error = str(e)
                print(f"DEBUG: Code validation FAILED on attempt {attempt + 1}: {e}")
                
                if attempt == max_code_attempts - 1:
                    # Final attempt failed, raise the error
                    raise ValueError(f"Code generation failed after {max_code_attempts} attempts. Last error: {last_code_error}")
                
                # Continue to next attempt
                continue
        
        if code is None:
            raise ValueError("Code generation failed - no valid code produced")
            
        return code.strip(), script

