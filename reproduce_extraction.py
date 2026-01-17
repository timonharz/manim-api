
import sys
import unittest
from llm_service import LLMService

class TestLLMExtraction(unittest.TestCase):
    def setUp(self):
        self.service = LLMService()

    def test_extract_code_tags_indented(self):
        # Case 1: Code inside tags, but indented (common issue)
        response = """
        Here is the code:
        [CODE]
            from manimlib import *
            class Test(Scene):
                def construct(self):
                    pass
        [/CODE]
        """
        extracted = self.service._extract_code(response)
        self.assertIn("from manimlib import *", extracted)
        self.assertFalse(extracted.startswith("    ")) # Should be dedented
        # First line should be imports
        self.assertTrue(extracted.strip().startswith("from manimlib import *"))

    def test_extract_markdown_blocks(self):
        # Case 2: Markdown blocks
        response = """
        Sure!
        ```python
        from manimlib import *
        class MyScene(Scene):
            pass
        ```
        """
        extracted = self.service._extract_code(response)
        self.assertIn("class MyScene(Scene):", extracted)
        self.assertTrue(extracted.startswith("from manimlib import *"))

    def test_heuristic_fragment(self):
        # Case 3: Just code, no tags, maybe indented
        response = """
            from manimlib import *
            
            class Fragment(Scene):
                def construct(self):
                    self.play(Write(Text("Hi")))
        """
        extracted = self.service._extract_code(response)
        self.assertTrue(extracted.strip().startswith("from manimlib import *"))
        self.assertIn("class Fragment(Scene):", extracted)

    def test_post_process_sanitization(self):
        # Case: Text replacement and missing imports
        code = r"""
        class MyScene(Scene):
            def construct(self):
                t = Tex(r"\text{Hello}")
                a = MathTex("x")
                self.play(Create(t))
        """
        processed = self.service._post_process_code(code)
        
        self.assertIn("from manimlib import *", processed) # Added imports
        self.assertIn(r"\mathrm{Hello}", processed) # Fixed text
        self.assertNotIn(r"\text{Hello}", processed)
        self.assertIn("Tex", processed) # Fixed MathTex
        self.assertIn("Tex", processed) # Fixed MathTex
        self.assertNotIn("MathTex", processed)
        self.assertIn("ShowCreation", processed) # Fixed Create

    def test_missing_scene_class_wrapping(self):
        # Case: Stateless code fragment
        code = """
        c = Circle()
        self.play(ShowCreation(c))
        """
        processed = self.service._post_process_code(code)
        
        self.assertIn("class GeneratedScene(Scene):", processed)
        self.assertIn("def construct(self):", processed)
        self.assertIn("    c = Circle()", processed) # Should be indented now

if __name__ == "__main__":
    unittest.main()
