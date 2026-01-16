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
3. Define ONE main Scene class that will be rendered. It MUST be the LAST class in the file.
4. Include `self.add_sound("narration.mp3")` at the START of the `construct` method.
5. Use standard color constants (RED, BLUE, GREEN, YELLOW, WHITE, etc.) or HEX codes like "#FF5733".
6. Use `Write()` for Tex/Text objects, `ShowCreation()` for shapes/lines.
7. Use `VGroup()` to group related objects and animate them together.
8. Add explanatory labels with Tex() positioned using `.next_to()` or `.to_edge()`.
9. Use `self.wait()` between major animation steps for proper pacing with narration.
10. For complex topics, break the animation into sections using helper methods.

## STYLE GUIDELINES:
- Create visually engaging animations with smooth transitions
- Use colors strategically to highlight important elements
- Add mathematical notation on screen to reinforce spoken explanations
- Build complexity gradually - introduce elements one at a time
- Use FadeIn/FadeOut for smooth scene transitions
"""

        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="openai/gpt-oss-120b",
            reasoning_effort="high",
            temperature=0.7,
            max_completion_tokens=8192
        )

        content = completion.choices[0].message.content

        try:
            script = content.split("[SCRIPT]")[1].split("[/SCRIPT]")[0].strip()
            code = content.split("[CODE]")[1].split("[/CODE]")[0].strip()
            
            # Clean up code block markers if present
            if code.startswith("```"):
                lines = code.split("\n")
                # Remove first line (```python) and last line (```)
                code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            # Validate the code has required import
            if "from manimlib import" not in code:
                code = "from manimlib import *\n\n" + code
                
            return code.strip(), script
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}\n\nRaw response:\n{content[:500]}")

