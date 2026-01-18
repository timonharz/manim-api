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
### Circles and Arcs
```python
Circle(radius=1.0, color=BLUE, fill_opacity=0.5, stroke_width=2)
Dot(point=ORIGIN, radius=0.08, color=WHITE)
Arc(start_angle=0, angle=PI/2, radius=1.0, arc_center=ORIGIN)
Annulus(inner_radius=1.0, outer_radius=2.0, color=BLUE)
```
### Lines and Arrows
```python
Line(start=LEFT, end=RIGHT, color=WHITE)
DashedLine(start=LEFT, end=RIGHT)
Arrow(start=LEFT, end=RIGHT, buff=0)
Vector(direction=UP)  # Starts at ORIGIN
DoubleArrow(LEFT, RIGHT)
```
### Polygons
```python
Rectangle(width=4.0, height=2.0)
Square(side_length=2.0)
Triangle()
Polygon(UP, LEFT, RIGHT)  # Custom vertices
RegularPolygon(n=6)
```
""",

    "text_latex": """
## Text and LaTeX (from manimlib.mobject.svg.tex_mobject)

### Tex (Mathematical Equations)
Use `Tex` for any math. It uses LaTeX `align*` environment by default.
```python
# Single expression
eq = Tex(r"E = mc^2", color=YELLOW)

# Multiple parts for coloring/animating separately
eq = Tex(r"a^2", r"+", r"b^2", r"=", r"c^2")
eq.set_color_by_tex("a", RED)
```

### Text (Plain Text)
Use `Text` for regular words. Do NOT use `\text{}` inside `Tex` for long sentences.
```python
title = Text("Pythagorean Theorem", font="Arial", font_size=48)
subtitle = Text("A fundamental relation", font_size=32)
```

### Positioning
```python
label.next_to(obj, UP, buff=0.2)
label.to_edge(UP)
label.to_corner(UL)
```
""",

    "coordinate_systems": """
## Graphs and Coordinate Systems (ManimGL ONLY - NOT community manim!)

### Axes (2D Plotting) - CORRECT ManimGL SYNTAX
IMPORTANT: ManimGL Axes does NOT have `tips`, `tip_shape`, or `include_numbers` parameters!
```python
# Basic Axes (CORRECT)
axes = Axes(
    x_range=(-3, 3, 1),   # (min, max, step)
    y_range=(-2, 2, 0.5),
    width=10,
    height=6,
    axis_config={"include_tip": True}  # For arrow tips
)
axes.add_coordinate_labels()  # Add numbers to axes

# WRONG (will crash):
# axes = Axes(x_range=..., tips=True)  # NO tips parameter!
# axes = Axes(x_range=..., axis_config={"tip_shape": ...})  # NO tip_shape!
```

### NumberPlane (Grid Background)
```python
plane = NumberPlane(
    x_range=(-8, 8),
    y_range=(-5, 5),
    background_line_style={
        "stroke_color": BLUE_D,
        "stroke_width": 1,
        "stroke_opacity": 0.5
    }
)
```

### Graphing Functions
```python
# Plot a function
graph = axes.get_graph(lambda x: x**2, color=YELLOW)

# Add label to graph
label = axes.get_graph_label(graph, "f(x) = x^2")

# Coordinate conversions
point = axes.c2p(2, 4)           # coords -> screen position
point_on_curve = axes.i2gp(2, graph)  # x value -> point on curve
```

### 3D Axes (ThreeDAxes)
```python
axes = ThreeDAxes(
    x_range=(-6, 6, 1),
    y_range=(-5, 5, 1),
    z_range=(-4, 4, 1)
)
```
""",

    "3d_scenes": """
## 3D Scenes (ThreeDScene)

### Setup
```python
class My3DScene(ThreeDScene):
    def construct(self):
        # Set generic camera view
        self.frame.set_euler_angles(
            theta=-30 * DEGREES,
            phi=70 * DEGREES
        )
        
        # 3D Shapes
        sphere = Sphere(radius=1.0)
        cube = Cube(side_length=2)
        axes = ThreeDAxes()
        
        self.play(ShowCreation(axes))
        self.play(FadeIn(sphere))
        
        # Animate Camera
        self.play(
            self.frame.animate.increment_theta(45 * DEGREES),
            run_time=3
        )
```
### Fixed Overlay (IMPORTANT)
To keep text static while camera moves, use `fix_in_frame()`:
```python
title = Text("My 3D Plot")
title.to_edge(UP)
title.fix_in_frame()
self.add(title)
```
""",

    "animations_basic": """
## Core Animations

### Creation
```python
self.play(ShowCreation(circle))  # Draw stroke
self.play(Write(text))           # Write text/latex
self.play(FadeIn(obj))           # Simple fade
self.play(DrawBorderThenFill(sq))
```

### Transformation
```python
self.play(Transform(circle, square))  # Morph
self.play(ReplacementTransform(old, new))
self.play(obj.animate.shift(RIGHT * 2).scale(1.5))  # .animate syntax
```

### Indication
```python
self.play(Indicate(obj))  # Flash color/scale
self.play(Flash(point))
self.play(FocusOn(point))
```

### Grouping and Timing
```python
self.play(
    AnimationGroup(
        Write(text),
        ShowCreation(line),
        lag_ratio=0.5
    )
)
self.wait()
```
""",

    "updaters": """
## Updaters and ValueTrackers
Use these for dynamic animations where values change over time.

### ValueTracker
```python
# 1. Create tracker
t = ValueTracker(0)

# 2. Add updater to mobject dependent on tracker
dot = Dot()
dot.add_updater(lambda m: m.move_to(
    axes.c2p(t.get_value(), t.get_value()**2)
))

# 3. Animate the tracker
self.add(dot)
self.play(t.animate.set_value(5), run_time=4)
```

### General Updaters
```python
# Rotate continuously
mob.add_updater(lambda m, dt: m.rotate(dt * PI))
# Stop
mob.clear_updaters()
```
""",

    "vgroup": """
## Grouping (VGroup)
Use `VGroup` to bundle mobjects.
```python
# Create and styling
circle = Circle()
square = Square()
group = VGroup(circle, square).set_color(RED)

# Arrange automatically
group.arrange(RIGHT, buff=1.0)

# Add to scene
self.play(ShowCreation(group))
```
""",

    "mobject_methods": """
## Common Mobject Methods
```python
obj.shift(UP * 2 + RIGHT)
obj.scale(2.0)
obj.rotate(45 * DEGREES)
obj.set_color(RED)
obj.set_opacity(0.5)

# Relative positioning
obj.next_to(other_obj, DOWN, buff=0.5)
obj.move_to(other_obj.get_center())
obj.align_to(other_obj, UP)
```
""",

    "constants_colors": """
## Constants & Colors
### Colors
`BLUE`, `TEAL`, `GREEN`, `YELLOW`, `GOLD`, `RED`, `MAROON`, `PURPLE`, `PINK`, `ORANGE`, `GREY`, `WHITE`, `BLACK`
Variations: `BLUE_A` (light) to `BLUE_E` (dark).

### Math Constants
`PI`, `TAU`, `DEGREES` (use `90 * DEGREES`)
`UP`, `DOWN`, `LEFT`, `RIGHT`, `UL`, `UR`, `DL`, `DR`, `ORIGIN`
""",

    "animations_composition": """
## Composing Animations
```python
# Lagged Start
self.play(
    AnimationGroup(
        *[ShowCreation(mob) for mob in mobjects],
        lag_ratio=0.1
    )
)

# Sequential
self.play(
    Succession(
        Write(text),
        FadeOut(text),
        ShowCreation(new_obj)
    )
)
```
""",

    "rate_functions": """
## Rate Functions (Easing)
Control animation speed.
`linear`, `smooth` (default), `there_and_back`, `rush_into`, `rush_from`, `slow_into`
```python
self.play(MoveToTarget(obj), rate_func=linear)
```
"""
}

# =============================================================================
# KEYWORD TO SECTION MAPPING
# =============================================================================

KEYWORD_MAPPINGS: Dict[str, List[str]] = {
    # Geometry
    "circle": ["geometry_basic"],
    "square": ["geometry_basic"],
    "rectangle": ["geometry_basic"],
    "triangle": ["geometry_basic"],
    "polygon": ["geometry_basic"],
    "line": ["geometry_basic"],
    "arrow": ["geometry_basic"],
    "vector": ["geometry_basic"],
    "shape": ["geometry_basic"],
    
    # Text/Math
    "text": ["text_latex"],
    "write": ["text_latex", "animations_basic"],
    "equation": ["text_latex"],
    "formula": ["text_latex"],
    "latex": ["text_latex"],

    # Graphs
    "graph": ["coordinate_systems"],
    "plot": ["coordinate_systems"],
    "axes": ["coordinate_systems"],
    "grid": ["coordinate_systems"],
    "numberplane": ["coordinate_systems"],
    "function": ["coordinate_systems"],
    "curve": ["coordinate_systems"],

    # 3D
    "3d": ["3d_scenes"],
    "three dimensions": ["3d_scenes"],
    "camera": ["3d_scenes"],
    
    # Composition
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
    "updater": ["updaters"],
    "dynamic": ["updaters"],
    "tracker": ["updaters"],
    "value tracker": ["updaters"],
    "follow": ["updaters"],
    "attached": ["updaters"],
    "real-time": ["updaters"],
    
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
    baseline_sections = ["scene_methods", "constants_colors", "mobject_methods", "vgroup"]
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


