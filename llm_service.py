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

        # RAG-style knowledge base extracted from manimlib source code
        manim_knowledge = """
## AVAILABLE MANIMLIB CLASSES AND FUNCTIONS

### Import (REQUIRED - use exactly this):
from manimlib import *

### Mobjects (Shapes):
- Circle(radius=1.0, color=BLUE)
- Square(side_length=2.0, color=WHITE)
- Rectangle(width=4.0, height=2.0)
- Line(start=LEFT, end=RIGHT)
- Arrow(start=LEFT, end=RIGHT)
- Dot(point=ORIGIN, radius=0.08)
- Arc(start_angle=0, angle=TAU/4, radius=1.0)
- Polygon(*vertices)
- RegularPolygon(n=6)
- Triangle()
- Ellipse(width=2, height=1)

### Text & Math:
- Text("Hello", font_size=48)
- Tex(r"\\LaTeX")
- MathTex(r"E = mc^2")

### Positioning Constants:
- ORIGIN, UP, DOWN, LEFT, RIGHT
- UL (up-left), UR (up-right), DL (down-left), DR (down-right)

### Colors:
- BLUE, RED, GREEN, YELLOW, WHITE, BLACK, ORANGE, PURPLE, PINK, TEAL, GOLD, MAROON, GREY

### Animations:
- self.play(ShowCreation(mobject))  # Draw a shape
- self.play(Write(text))  # Write text
- self.play(FadeIn(mobject))
- self.play(FadeOut(mobject))
- self.play(Transform(source, target))
- self.play(ReplacementTransform(source, target))
- self.play(mobject.animate.shift(UP))
- self.play(mobject.animate.scale(2))
- self.play(mobject.animate.rotate(PI/2))
- self.play(mobject.animate.set_color(RED))

### Scene Methods:
- self.wait(duration=1)
- self.add(mobject)
- self.remove(mobject)
- self.add_sound("narration.mp3")

### Mobject Methods:
- mobject.shift(direction)
- mobject.move_to(point)
- mobject.next_to(other, direction)
- mobject.scale(factor)
- mobject.rotate(angle)
- mobject.set_color(color)
- mobject.set_fill(color, opacity)
- mobject.set_stroke(color, width)
"""

        system_prompt = f"""
You are an expert Manim animation developer. Your goal is to generate Python code using `manimlib` (ManimGL version) to visualize the user's request, and a corresponding narration script.

{manim_knowledge}

## OUTPUT FORMAT (follow exactly):

[SCRIPT]
... (The text script for the narration, plain text)
[/SCRIPT]

[CODE]
... (The Python code for the scene)
[/CODE]

## CRITICAL RULES:
1. Use ONLY `from manimlib import *`. NEVER use `manim`, `manif`, or any other library.
2. Define exactly ONE Scene class.
3. Include `self.add_sound("narration.mp3")` at the start of `construct`.
4. Keep the animation simple and focused.
5. Only use classes and methods listed above.
"""

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
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
