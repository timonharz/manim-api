"""
Manim Knowledge Base for RAG System

This module provides a comprehensive knowledge base of manimlib features
and a keyword-based retrieval system for augmenting LLM prompts.
"""

from typing import List, Dict, Set
import re

# =============================================================================
# KNOWLEDGE BASE SECTIONS
# =============================================================================

KNOWLEDGE_SECTIONS: Dict[str, str] = {
    
    "geometry_basic": """
## Basic Geometry (from manimlib.mobject.geometry)

### Circle
```python
Circle(radius=1.0, color=BLUE, fill_opacity=0.5, stroke_width=2)
circle.point_at_angle(PI/4)  # Get point on circle at angle
circle.get_radius()
```

### Dot / SmallDot
```python
Dot(point=ORIGIN, radius=0.08, color=WHITE)
SmallDot(point=ORIGIN)  # Smaller default radius
```

### Arc
```python
Arc(start_angle=0, angle=PI/2, radius=1.0, arc_center=ORIGIN)
ArcBetweenPoints(start, end, angle=TAU/4)
```

### Ellipse
```python
Ellipse(width=2.0, height=1.0)
```
""",

    "geometry_lines": """
## Lines and Arrows (from manimlib.mobject.geometry)

### Line
```python
Line(start=LEFT, end=RIGHT, color=WHITE, stroke_width=2)
DashedLine(start=LEFT, end=RIGHT, dash_length=0.1)
line.get_length()
line.get_angle()
```

### Arrow
```python
Arrow(start=LEFT, end=RIGHT, buff=0.25, stroke_width=6)
DoubleArrow(start=LEFT, end=RIGHT)  # Arrow on both ends
Vector(direction=UP)  # Arrow from ORIGIN
```

### CurvedArrow
```python
CurvedArrow(start_point, end_point, angle=TAU/4)
CurvedDoubleArrow(start_point, end_point)
```
""",

    "geometry_polygons": """
## Polygons and Rectangles (from manimlib.mobject.geometry)

### Rectangle / Square
```python
Rectangle(width=4.0, height=2.0, color=BLUE, fill_opacity=0.5)
Square(side_length=2.0)
RoundedRectangle(width=4.0, height=2.0, corner_radius=0.5)
```

### Polygon
```python
Polygon(point1, point2, point3, ...)  # From vertices
RegularPolygon(n=6, radius=1.0)  # n-sided regular polygon
Triangle()  # Equilateral triangle
Star(n=5, outer_radius=1.0, inner_radius=0.5)
```

### Sector / Annulus
```python
Sector(angle=PI/2, start_angle=0, inner_radius=0, outer_radius=1)
AnnularSector(inner_radius=1.0, outer_radius=2.0, angle=PI/2)
Annulus(inner_radius=1.0, outer_radius=2.0)
```
""",

    "text_latex": """
## Text and LaTeX (from manimlib.mobject.svg.tex_mobject)

### Tex (for LaTeX math)
```python
Tex(r"E = mc^2", font_size=48)
Tex(r"\\int_0^1 x^2 dx = \\frac{1}{3}")
Tex(r"a^2 + b^2 = c^2", color=YELLOW)

# Multiple parts
equation = Tex(r"a^2", r"+", r"b^2", r"=", r"c^2")
equation.set_color_by_tex("a", RED)
equation.set_color_by_tex("b", BLUE)
```

### MathTex (alias for Tex in manimgl)
```python
MathTex(r"\\sum_{n=1}^{\\infty} \\frac{1}{n^2} = \\frac{\\pi^2}{6}")
```

### TexText (for text with optional LaTeX)
```python
TexText("Hello World", font_size=48)
TexText(r"The formula $E=mc^2$ is famous")
```

### Text (plain text)
```python
Text("Plain text", font="Arial", font_size=48)
```
""",

    "coordinate_systems": """
## Coordinate Systems and Graphs (from manimlib.mobject.coordinate_systems)

### Axes
```python
axes = Axes(
    x_range=[-3, 3, 1],  # [min, max, step]
    y_range=[-2, 2, 1],
    width=10,
    height=6
)
axes.add_coordinate_labels()  # Add tick labels
```

### NumberPlane
```python
plane = NumberPlane(
    x_range=[-7, 7, 1],
    y_range=[-4, 4, 1],
    background_line_style={"stroke_opacity": 0.5}
)
```

### Graphing Functions
```python
# Plot a function
graph = axes.get_graph(lambda x: x**2, color=BLUE)
graph = axes.get_graph(lambda x: np.sin(x), x_range=[-PI, PI])

# Parametric curves
curve = axes.get_parametric_curve(
    lambda t: [np.cos(t), np.sin(t), 0],
    t_range=[0, TAU]
)

# Get point on graph
point = axes.input_to_graph_point(x=2, graph=graph)
# or shorthand: axes.i2gp(2, graph)

# Coordinates to point
point = axes.c2p(x, y)  # coords_to_point
x, y = axes.p2c(point)  # point_to_coords
```

### NumberLine
```python
number_line = NumberLine(x_range=[-5, 5, 1], include_numbers=True)
```
""",

    "3d_objects": """
## 3D Objects (from manimlib.mobject.three_dimensions)

### Basic 3D Shapes
```python
Sphere(radius=1.0, resolution=(101, 51))
Cylinder(radius=1.0, height=2.0, axis=OUT)
Cone(radius=1.0, height=2.0)
Torus(r1=3.0, r2=1.0)  # r1=major radius, r2=minor radius
```

### 3D Lines
```python
Line3D(start=ORIGIN, end=OUT * 2, width=0.05)
```

### Surfaces
```python
# Custom parametric surface
class MySurface(Surface):
    def uv_func(self, u, v):
        return [u, v, np.sin(u) * np.cos(v)]

surface = Surface(
    uv_func=lambda u, v: [u, v, u**2 + v**2],
    u_range=[-2, 2],
    v_range=[-2, 2],
    resolution=(50, 50)
)
SurfaceMesh(surface, resolution=(21, 11))  # Add mesh lines
```

### 3D Axes
```python
axes = ThreeDAxes(
    x_range=[-5, 5],
    y_range=[-5, 5],
    z_range=[-3, 3]
)
```
""",

    "animations_creation": """
## Creation Animations (from manimlib.animation.creation)

### ShowCreation - Draw shapes progressively
```python
self.play(ShowCreation(circle))  # Draw circle
self.play(ShowCreation(line, run_time=2))
```

### Write - For text and Tex
```python
self.play(Write(tex))  # Animate writing LaTeX
self.play(Write(text, run_time=2))
```

### DrawBorderThenFill
```python
self.play(DrawBorderThenFill(shape))  # Draw outline, then fill
```

### Uncreate - Reverse of ShowCreation
```python
self.play(Uncreate(circle))
```

### ShowIncreasingSubsets / ShowSubmobjectsOneByOne
```python
self.play(ShowIncreasingSubsets(vgroup))  # Show items one by one
```

### AddTextWordByWord
```python
self.play(AddTextWordByWord(text, time_per_word=0.2))
```
""",

    "animations_fading": """
## Fading Animations (from manimlib.animation.fading)

### FadeIn / FadeOut
```python
self.play(FadeIn(mobject))
self.play(FadeIn(mobject, shift=UP))  # Fade in from below
self.play(FadeIn(mobject, scale=0.5))  # Fade in while scaling up

self.play(FadeOut(mobject))
self.play(FadeOut(mobject, shift=DOWN))  # Fade out moving down
```

### FadeInFromPoint / FadeOutToPoint
```python
self.play(FadeInFromPoint(mobject, point=ORIGIN))
self.play(FadeOutToPoint(mobject, point=ORIGIN))
```

### FadeTransform - Morph between objects with fade
```python
self.play(FadeTransform(circle, square))
```

### VFadeIn / VFadeOut - For VMobjects with stroke
```python
self.play(VFadeIn(vmobject))
self.play(VFadeOut(vmobject))
```
""",

    "animations_transform": """
## Transform Animations (from manimlib.animation.transform)

### Transform - Morph one object into another
```python
self.play(Transform(circle, square))  # circle becomes square
```

### ReplacementTransform - Replace in scene
```python
self.play(ReplacementTransform(old, new))  # old removed, new added
```

### TransformFromCopy
```python
self.play(TransformFromCopy(source, target))  # Keep source, create target
```

### MoveToTarget
```python
mobject.generate_target()
mobject.target.shift(RIGHT * 2)
mobject.target.set_color(RED)
self.play(MoveToTarget(mobject))
```

### ApplyMethod
```python
self.play(ApplyMethod(mobject.shift, RIGHT))
self.play(ApplyMethod(mobject.set_color, RED))
# Or use mobject.animate syntax:
self.play(mobject.animate.shift(RIGHT).set_color(RED))
```

### Rotate / Rotating
```python
self.play(Rotate(mobject, angle=PI/2, about_point=ORIGIN))
```
""",

    "animations_indication": """
## Indication Animations (from manimlib.animation.indication)

### Indicate - Highlight temporarily
```python
self.play(Indicate(mobject, scale_factor=1.2, color=YELLOW))
```

### Flash - Radial flash effect
```python
self.play(Flash(point, color=YELLOW, flash_radius=0.5))
self.play(Flash(mobject.get_center()))
```

### CircleIndicate
```python
self.play(CircleIndicate(mobject, stroke_color=YELLOW))
```

### ShowPassingFlash
```python
self.play(ShowPassingFlash(path, time_width=0.2))
```

### Wiggle
```python
self.play(Wiggle(mobject, scale_value=1.1, rotation_angle=0.1))
```

### FocusOn
```python
self.play(FocusOn(point, opacity=0.2, color=GREY))
```
""",

    "animations_composition": """
## Animation Composition (from manimlib.animation.composition)

### AnimationGroup - Play animations together
```python
self.play(AnimationGroup(
    FadeIn(circle),
    FadeIn(square),
    lag_ratio=0.5  # Stagger start times
))
```

### Succession - Play one after another
```python
self.play(Succession(
    FadeIn(a),
    FadeIn(b),
    FadeIn(c)
))
```

### LaggedStart - Staggered animations
```python
self.play(LaggedStart(
    *[FadeIn(m) for m in mobjects],
    lag_ratio=0.2
))
```

### LaggedStartMap
```python
self.play(LaggedStartMap(FadeIn, vgroup, lag_ratio=0.1))
```
""",

    "scene_methods": """
## Scene Methods (from manimlib.scene.scene)

### Playing Animations
```python
self.play(animation)  # Play single animation
self.play(anim1, anim2)  # Play multiple simultaneously
self.play(animation, run_time=2)  # Custom duration
self.play(animation, rate_func=smooth)  # Custom easing
```

### Waiting
```python
self.wait()  # Wait 1 second
self.wait(2)  # Wait 2 seconds
self.wait_until(condition_func)  # Wait until condition
```

### Adding/Removing
```python
self.add(mobject)  # Add without animation
self.remove(mobject)  # Remove without animation
self.clear()  # Remove all mobjects
```

### Sound
```python
self.add_sound("narration.mp3")  # Add audio file
self.add_sound("effect.wav", time_offset=0.5)
```

### Camera (for 3D)
```python
self.set_camera_orientation(phi=75*DEGREES, theta=-45*DEGREES)
self.begin_ambient_camera_rotation(rate=0.1)
self.stop_ambient_camera_rotation()
self.move_camera(phi=60*DEGREES, theta=30*DEGREES, run_time=2)
```
""",

    "mobject_methods": """
## Mobject Methods (common to all mobjects)

### Positioning
```python
mobject.move_to(ORIGIN)  # Move center to point
mobject.move_to(other_mobject)  # Align centers
mobject.next_to(other, RIGHT, buff=0.5)  # Position relative to other
mobject.shift(UP * 2 + RIGHT)  # Move by vector
mobject.to_edge(LEFT, buff=0.5)  # Move to screen edge
mobject.to_corner(UL)  # Move to corner
mobject.align_to(other, UP)  # Align edges
mobject.center()  # Center on screen
```

### Styling
```python
mobject.set_color(RED)
mobject.set_fill(color=BLUE, opacity=0.5)
mobject.set_stroke(color=WHITE, width=2, opacity=1)
mobject.set_opacity(0.5)
mobject.set_style(fill_color=BLUE, stroke_color=WHITE)
```

### Transforming
```python
mobject.scale(2)  # Double size
mobject.scale(0.5, about_point=ORIGIN)  # Scale about point
mobject.rotate(PI/4)  # Rotate 45 degrees
mobject.rotate(PI/2, axis=RIGHT)  # 3D rotation
mobject.stretch(2, dim=0)  # Stretch horizontally
mobject.flip(axis=RIGHT)  # Mirror
```

### Copying and Info
```python
copy = mobject.copy()
center = mobject.get_center()
width = mobject.get_width()
height = mobject.get_height()
```
""",

    "constants_colors": """
## Constants and Colors (from manimlib.constants)

### Directional Constants
```python
UP = np.array([0, 1, 0])
DOWN = np.array([0, -1, 0])
LEFT = np.array([-1, 0, 0])
RIGHT = np.array([1, 0, 0])
ORIGIN = np.array([0, 0, 0])

# Diagonals
UL = UP + LEFT     # Upper Left
UR = UP + RIGHT    # Upper Right
DL = DOWN + LEFT   # Down Left
DR = DOWN + RIGHT  # Down Right

# 3D
IN = np.array([0, 0, -1])
OUT = np.array([0, 0, 1])
```

### Colors
```python
# Primary
RED, BLUE, GREEN, YELLOW, WHITE, BLACK

# Extended palette
GREY, GRAY, PURPLE, ORANGE, TEAL, GOLD, MAROON, PINK

# Shades (append _A through _E for light to dark)
BLUE_A, BLUE_B, BLUE_C, BLUE_D, BLUE_E
RED_A, RED_B, RED_C, RED_D, RED_E
# etc.

# Using hex colors
mobject.set_color("#FF5733")
```

### Math Constants
```python
PI = np.pi
TAU = 2 * PI
DEGREES = PI / 180  # Multiply to convert degrees to radians
```
""",

    "vgroup": """
## VGroup and Grouping (from manimlib.mobject.types.vectorized_mobject)

### VGroup - Group VMobjects together
```python
group = VGroup(circle, square, triangle)

# Access items
group[0]  # First item
group[-1]  # Last item

# Add/remove
group.add(new_mobject)
group.remove(mobject)

# Apply to all
group.set_color(RED)
group.shift(UP)
group.arrange(RIGHT, buff=0.5)  # Arrange in a row
group.arrange(DOWN, buff=0.3)  # Arrange in a column
group.arrange_in_grid(rows=2, cols=3)
```

### Creating groups dynamically
```python
dots = VGroup(*[Dot() for _ in range(10)])
dots.arrange(RIGHT, buff=0.2)

# With list comprehension
circles = VGroup(*[Circle(radius=0.2 + 0.1*i) for i in range(5)])
```
""",

    "rate_functions": """
## Rate Functions (Easing) (from manimlib.utils.rate_functions)

### Common rate functions
```python
self.play(animation, rate_func=linear)  # Constant speed
self.play(animation, rate_func=smooth)  # Smooth start and end
self.play(animation, rate_func=rush_into)  # Fast then slow
self.play(animation, rate_func=rush_from)  # Slow then fast
self.play(animation, rate_func=there_and_back)  # Go and return
self.play(animation, rate_func=double_smooth)  # Extra smooth
self.play(animation, rate_func=lingering)  # Slow at end
```
""",

    "multi_scene_pattern": """
## Multi-Scene Animation Patterns

### Structure for complex animations
```python
from manimlib import *

class ComplexAnimation(Scene):
    def construct(self):
        self.add_sound("narration.mp3")
        
        # Part 1: Introduction
        self.intro_section()
        
        # Part 2: Main demonstration
        self.main_demonstration()
        
        # Part 3: Conclusion
        self.conclusion()
    
    def intro_section(self):
        title = Tex(r"Topic Title", font_size=72)
        self.play(Write(title))
        self.wait()
        self.play(FadeOut(title))
    
    def main_demonstration(self):
        # Create objects
        axes = Axes(x_range=[-3, 3], y_range=[-2, 2])
        graph = axes.get_graph(lambda x: x**2, color=BLUE)
        
        # Animate
        self.play(ShowCreation(axes))
        self.play(ShowCreation(graph))
        
        # Add explanation
        label = Tex(r"f(x) = x^2")
        label.next_to(graph, UP)
        self.play(Write(label))
        self.wait()
    
    def conclusion(self):
        final_text = TexText("Thank you!")
        self.play(FadeIn(final_text))
        self.wait(2)
```

### Tips for complex animations:
1. Break into logical sections/methods
2. Use self.wait() for pacing with narration
3. Add explanatory Tex labels
4. Use FadeIn/FadeOut for smooth transitions
5. Scale complexity to match the topic
"""
}

# =============================================================================
# KEYWORD TO SECTION MAPPING
# =============================================================================

KEYWORD_MAPPINGS: Dict[str, List[str]] = {
    # Geometry
    "circle": ["geometry_basic", "mobject_methods"],
    "dot": ["geometry_basic"],
    "arc": ["geometry_basic"],
    "ellipse": ["geometry_basic"],
    "line": ["geometry_lines"],
    "arrow": ["geometry_lines"],
    "vector": ["geometry_lines"],
    "rectangle": ["geometry_polygons"],
    "square": ["geometry_polygons"],
    "polygon": ["geometry_polygons"],
    "triangle": ["geometry_polygons"],
    "star": ["geometry_polygons"],
    "sector": ["geometry_polygons"],
    "annulus": ["geometry_polygons"],
    "shape": ["geometry_basic", "geometry_polygons"],
    
    # Text
    "text": ["text_latex"],
    "tex": ["text_latex"],
    "latex": ["text_latex"],
    "math": ["text_latex", "coordinate_systems"],
    "equation": ["text_latex"],
    "formula": ["text_latex"],
    "label": ["text_latex"],
    
    # Graphs and coordinates
    "graph": ["coordinate_systems"],
    "plot": ["coordinate_systems"],
    "function": ["coordinate_systems"],
    "axes": ["coordinate_systems"],
    "axis": ["coordinate_systems"],
    "coordinate": ["coordinate_systems"],
    "plane": ["coordinate_systems"],
    "number line": ["coordinate_systems"],
    "x-axis": ["coordinate_systems"],
    "y-axis": ["coordinate_systems"],
    "sine": ["coordinate_systems"],
    "cosine": ["coordinate_systems"],
    "parabola": ["coordinate_systems"],
    
    # 3D
    "3d": ["3d_objects", "scene_methods"],
    "sphere": ["3d_objects"],
    "cylinder": ["3d_objects"],
    "cone": ["3d_objects"],
    "torus": ["3d_objects"],
    "surface": ["3d_objects"],
    "camera": ["scene_methods"],
    "rotate camera": ["scene_methods"],
    
    # Animations
    "animate": ["animations_creation", "animations_transform"],
    "animation": ["animations_creation", "animations_transform", "animations_composition"],
    "create": ["animations_creation"],
    "write": ["animations_creation"],
    "draw": ["animations_creation"],
    "fade": ["animations_fading"],
    "appear": ["animations_fading"],
    "disappear": ["animations_fading"],
    "transform": ["animations_transform"],
    "morph": ["animations_transform"],
    "move": ["animations_transform", "mobject_methods"],
    "indicate": ["animations_indication"],
    "flash": ["animations_indication"],
    "highlight": ["animations_indication"],
    "wiggle": ["animations_indication"],
    "group": ["animations_composition", "vgroup"],
    "sequence": ["animations_composition"],
    "together": ["animations_composition"],
    
    # General
    "color": ["constants_colors", "mobject_methods"],
    "position": ["mobject_methods", "constants_colors"],
    "scale": ["mobject_methods"],
    "rotate": ["mobject_methods", "animations_transform"],
    "vgroup": ["vgroup"],
    "arrange": ["vgroup"],
    "easing": ["rate_functions"],
    "smooth": ["rate_functions"],
    
    # Complex topics  
    "explain": ["multi_scene_pattern", "text_latex"],
    "theorem": ["multi_scene_pattern", "text_latex", "geometry_basic"],
    "proof": ["multi_scene_pattern", "text_latex"],
    "step by step": ["multi_scene_pattern"],
    "tutorial": ["multi_scene_pattern"],
    "demonstration": ["multi_scene_pattern"],
    "fourier": ["coordinate_systems", "multi_scene_pattern"],
    "calculus": ["coordinate_systems", "text_latex"],
    "derivative": ["coordinate_systems", "text_latex"],
    "integral": ["coordinate_systems", "text_latex"],
    "pythagorean": ["geometry_polygons", "text_latex", "multi_scene_pattern"],
    "pythagoras": ["geometry_polygons", "text_latex", "multi_scene_pattern"],
}


# =============================================================================
# RETRIEVAL FUNCTIONS
# =============================================================================

def retrieve_relevant_knowledge(prompt: str, max_sections: int = 6) -> str:
    """
    Retrieve relevant manimlib knowledge based on the user's prompt.
    
    Uses keyword matching to find relevant documentation sections.
    
    Args:
        prompt: The user's animation prompt
        max_sections: Maximum number of sections to return
        
    Returns:
        A string containing relevant manimlib documentation
    """
    prompt_lower = prompt.lower()
    
    # Find matching sections based on keywords
    section_scores: Dict[str, int] = {}
    
    for keyword, sections in KEYWORD_MAPPINGS.items():
        if keyword in prompt_lower:
            for section in sections:
                section_scores[section] = section_scores.get(section, 0) + 1
    
    # Always include these baseline sections
    baseline_sections = ["scene_methods", "constants_colors", "mobject_methods"]
    for section in baseline_sections:
        section_scores[section] = section_scores.get(section, 0) + 0.5
    
    # Sort by score and take top sections
    sorted_sections = sorted(section_scores.items(), key=lambda x: -x[1])
    top_sections = [s[0] for s in sorted_sections[:max_sections]]
    
    # If no keywords matched, include a broad selection
    if not top_sections:
        top_sections = [
            "geometry_basic",
            "text_latex",
            "animations_creation",
            "animations_transform",
            "scene_methods",
            "multi_scene_pattern"
        ]
    
    # Build the knowledge string
    knowledge_parts = []
    for section in top_sections:
        if section in KNOWLEDGE_SECTIONS:
            knowledge_parts.append(KNOWLEDGE_SECTIONS[section])
    
    return "\n".join(knowledge_parts)


def get_all_knowledge() -> str:
    """Return all knowledge sections combined."""
    return "\n\n".join(KNOWLEDGE_SECTIONS.values())


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    # Test retrieval
    test_prompts = [
        "Explain the Pythagorean theorem with a triangle",
        "Animate a sine wave graph",
        "Create a 3D sphere rotating",
        "Show a circle transforming into a square",
    ]
    
    for prompt in test_prompts:
        print(f"\n{'='*60}")
        print(f"Prompt: {prompt}")
        print(f"{'='*60}")
        knowledge = retrieve_relevant_knowledge(prompt)
        print(f"Retrieved knowledge ({len(knowledge)} chars):")
        print(knowledge[:500] + "..." if len(knowledge) > 500 else knowledge)
