import os
from typing import Tuple
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.default_api_key = os.getenv("GROQ_API_KEY")

    def generate_manim_content(self, prompt: str, api_key: str = None) -> Tuple[str, str]:
        key_to_use = api_key or self.default_api_key
        if not key_to_use:
            raise ValueError("Groq API key is required.")
            
        client = Groq(api_key=key_to_use)

        manim_knowledge = """
## AVAILABLE MANIMLIB CLASSES
- Circle(radius=1.0, color=BLUE)
- Square(side_length=2.0)
- Rectangle(width=4.0, height=2.0)
- Line(start=LEFT, end=RIGHT)
- Arrow(start=LEFT, end=RIGHT)
- Tex(r"\\LaTeX")
- MathTex(r"E = mc^2")
- self.play(ShowCreation(mobj)), self.play(Write(text)), self.play(FadeIn(mobj)), self.play(Transform(src, tar))
- self.wait(duration)
- self.add_sound("narration.mp3")
"""

        system_prompt = f"""
You are an expert Manim animation developer. Generate Python code using `manimlib` (ManimGL) and a narration script.

{manim_knowledge}

## OUTPUT FORMAT:
[SCRIPT]
(Plain text script)
[/SCRIPT]

[CODE]
(Python code)
[/CODE]

## CRITICAL RULES (VIOLATION = SYSTEM CRASH):
1. Use ONLY `from manimlib import *`. 
2. NEVER use `import manim` or `from manim import ...`.
3. NEVER use `import manif` or `from manif import ...`.
4. YOU MUST use `from manimlib import *` as the first line.
5. Define the Scene class. You may define helper classes, but the MAIN Scene class must be the LAST class defined.
6. Include `self.add_sound("narration.mp3")` at the start of the main `construct` method.
7. Use standard colors (RED, BLUE, GREEN) or HEX codes (e.g. "#FF0000").
8. Do NOT use `ShowCreation` on Text objects if not sure, use `Write` or `FadeIn`.
"""

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            # Use a high-performance Groq model
            model="llama-3.3-70b-versatile"
        )

        content = completion.choices[0].message.content

        try:
            script = content.split("[SCRIPT]")[1].split("[/SCRIPT]")[0].strip()
            code = content.split("[CODE]")[1].split("[/CODE]")[0].strip()
            
            if code.startswith("```"):
                code = "\n".join(code.split("\n")[1:-1])
                
            return code.strip(), script
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}")
