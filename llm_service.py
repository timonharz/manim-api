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

    def generate_manim_content(self, prompt: str, api_key: str) -> Tuple[str, str]:
        """
        Generate Manim animation code and narration script from a prompt.
        
        Uses RAG to retrieve relevant manimlib documentation based on the prompt,
        then generates code that uses appropriate classes and methods.
        
        Args:
            prompt: User's animation request
            api_key: Groq API key (required)
            
        Returns:
            Tuple of (code, script) where code is the Python/Manim code
            and script is the narration text.
        """
        if not api_key:
            raise ValueError("Groq API key is required.")
            
        client = Groq(api_key=api_key)

        # RAG: Retrieve relevant manimlib knowledge based on prompt
        retrieved_knowledge = retrieve_relevant_knowledge(prompt, max_sections=6)

        system_prompt = f"""You are an expert Manim animation developer. Generate Python code using `manimlib` (ManimGL) and a detailed narration script.

## RELEVANT MANIMLIB DOCUMENTATION FOR THIS REQUEST:
{retrieved_knowledge}

## OUTPUT FORMAT:
[SCRIPT]
(A detailed, multi-paragraph narration script that explains the concept step-by-step.
This will be converted to audio, so write naturally as if speaking to a student.
Include pauses by writing "..." where appropriate.)
[/SCRIPT]

[CODE]
(Python code using manimlib. Create complex, engaging animations.
Break the animation into logical sections with methods if the topic is complex.
Use Tex/MathTex for mathematical explanations on screen.
Match animation timing to the narration script using self.wait() calls.)
[/CODE]

## CRITICAL RULES (VIOLATION = SYSTEM CRASH):
1. Use ONLY `from manimlib import *` as the FIRST import line.
2. NEVER use `import manim`, `from manim import ...`, `import manif`, or `from manif import ...`.
3. You may define multiple Scene classes. They will be rendered sequentially and stitched together. This is useful for breaking down complex topics.
4. Include `self.add_sound("narration.mp3")` at the START of the `construct` method.
5. Use standard color constants (RED, BLUE, GREEN, YELLOW, WHITE, etc.) or HEX codes like "#FF5733".
6. Use `Write()` for Tex/Text objects, `ShowCreation()` for shapes/lines.
7. Use `VGroup()` to group related objects and animate them together.
8. Add explanatory labels with Tex() positioned using `.next_to()` or `.to_edge()`.
9. Use `self.wait()` between major animation steps for proper pacing with narration.
10. For complex topics, break the animation into sections using helper methods.
11. FOR 3D SCENES: Inherit from `ThreeDScene`, NOT `Scene`. Example: `class My3DScene(ThreeDScene):`
12. FOR 3D CAMERA: Use `self.frame.set_euler_angles(theta=X, phi=Y)` to set camera angles. 
    NEVER use `set_camera_orientation()` - IT DOES NOT EXIST in manimgl!
13. FOR 3D TEXT OVERLAYS: Use `.fix_in_frame()` on Text/Tex that should stay fixed on screen.

## STYLE GUIDELINES:
- Create visually engaging animations with smooth transitions
- Use colors strategically to highlight important elements
- Add mathematical notation on screen to reinforce spoken explanations
- Build complexity gradually - introduce elements one at a time
- Use FadeIn/FadeOut for smooth scene transitions
- In 3D scenes, use `.fix_in_frame()` for titles/labels that shouldn't rotate with camera

## COMMON MISTAKES TO AVOID (VERY IMPORTANT):
- NEVER use `always_redraw(...)`. It DOES NOT EXIST in manimlib. Instead, use `mobject.add_updater(lambda m: m.become(...))` or `f_always(m.move_to, dot)`.
- NEVER use `ValueTracker().animate.set_value(...)`. Instead, use `tracker.animate.set_value(...)` (without the .animate if manimlib version is older, but usually tracker.animate works in manimgl).
- NEVER use `self.set_camera_orientation()`. Instead use `self.frame.set_euler_angles()`.
- Use `ShowCreation` for shapes, not `Create`.
- Use `Write` for Tex, not `AddTextWordByWord` (unless specifically asked for typing effect).
- Use `MathTex` or `Tex` for all mathematical formulas.
"""

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="openai/gpt-oss-120b",
            temperature=0.7,
            max_completion_tokens=8192
        )

        content = completion.choices[0].message.content

        # Robust regex-based parsing
        import re
        
        # Step 1: Strip common markdown formatting around tags
        # Handle bold/italic markers
        for marker in ['**', '*', '`']:
            content = content.replace(f"{marker}[SCRIPT]{marker}", "[SCRIPT]")
            content = content.replace(f"{marker}[/SCRIPT]{marker}", "[/SCRIPT]")
            content = content.replace(f"{marker}[CODE]{marker}", "[CODE]")
            content = content.replace(f"{marker}[/CODE]{marker}", "[/CODE]")
        
        # Step 2: More flexible regex that allows whitespace around tags
        script_match = re.search(r"\[\s*SCRIPT\s*\](.*?)\[\s*/SCRIPT\s*\]", content, re.DOTALL | re.IGNORECASE)
        code_match = re.search(r"\[\s*CODE\s*\](.*?)\[\s*/CODE\s*\]", content, re.DOTALL | re.IGNORECASE)

        if not script_match or not code_match:
            # Fallback: check for markdown code blocks if [CODE] is missing
            if not code_match:
                code_match = re.search(r"```python(.*?)```", content, re.DOTALL)
            
            if not script_match or not code_match:
                # Debug: Show what we found
                has_script_open = "[SCRIPT]" in content.upper() or "[ SCRIPT ]" in content.upper()
                has_script_close = "[/SCRIPT]" in content.upper() or "[ /SCRIPT ]" in content.upper()
                has_code_open = "[CODE]" in content.upper() or "[ CODE ]" in content.upper()
                has_code_close = "[/CODE]" in content.upper() or "[ /CODE ]" in content.upper()
                
                debug_info = f"Tags found: SCRIPT open={has_script_open}, close={has_script_close}, CODE open={has_code_open}, close={has_code_close}"
                raise ValueError(f"Failed to parse LLM response. {debug_info}\n\nRaw response (first 1000 chars):\n{content[:1000]}...")

        script = script_match.group(1).strip()
        code = code_match.group(1).strip()

        # Clean up code block markers if accidentally included inside [CODE]
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines).strip()
        
        # Sanitize code: Replace problematic unicode characters with ASCII equivalents
        # Replace en-dash (U+2013) and em-dash (U+2014) with hyphen
        code = code.replace('–', '-').replace('—', '-')
        # Replace smart quotes with regular quotes
        code = code.replace('"', '"').replace('"', '"')
        code = code.replace(''', "'").replace(''', "'")
        
        # Validate the code has required import
        if "from manimlib import" not in code:
            code = "from manimlib import *\n\n" + code
            
        return code.strip(), script

