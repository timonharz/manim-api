"""
Render service for Manim animations.

This module handles the actual rendering of Manim code to video files.
"""

import tempfile
import uuid
import os
import sys
import importlib.util
import shutil
from pathlib import Path
from typing import Optional
from addict import Dict

# Ensure manimlib is importable
sys.path.insert(0, str(Path(__file__).parent))

from manimlib.scene.scene import Scene
from manimlib.config import manim_config, load_yaml, get_manim_dir
from manimlib.utils.dict_ops import merge_dicts_recursively


QUALITY_MAP = {
    "low": (854, 480),
    "medium": (1280, 720),
    "high": (1920, 1080),
    "4k": (3840, 2160),
}

FORMAT_MAP = {
    "mp4": ".mp4",
    "gif": ".gif",
    "mov": ".mov",
}


class RenderResult:
    """Result of a render operation."""
    
    def __init__(self, video_path: Path, temp_dir: Path, success: bool, error: Optional[str] = None):
        self.video_path = video_path
        self.temp_dir = temp_dir
        self.success = success
        self.error = error
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)


def find_scene_class(module, scene_name: Optional[str] = None):
    """Find the scene class to render from the module."""
    import inspect
    
    scene_classes = []
    for name, obj in inspect.getmembers(module):
        if (inspect.isclass(obj) and 
            issubclass(obj, Scene) and 
            obj is not Scene and
            obj.__module__ == module.__name__):
            scene_classes.append((name, obj))
    
    if not scene_classes:
        raise ValueError("No Scene classes found in the provided code")
    
    if scene_name:
        for name, cls in scene_classes:
            if name == scene_name:
                return cls
        raise ValueError(f"Scene '{scene_name}' not found. Available scenes: {[n for n, _ in scene_classes]}")
    
    # Return the last defined scene (typically the main one)
    return scene_classes[-1][1]


def render_code(
    code: str,
    scene_name: Optional[str] = None,
    quality: str = "medium",
    format: str = "mp4"
) -> RenderResult:
    """
    Render Manim code and return the path to the output video.
    
    Args:
        code: The Python code containing Manim scene definitions
        scene_name: Optional name of the specific scene to render
        quality: Video quality (low, medium, high, 4k)
        format: Output format (mp4, gif, mov)
    
    Returns:
        RenderResult containing the path to the video and cleanup method
    """
    # Create temporary directory for this render
    temp_dir = Path(tempfile.mkdtemp(prefix="manim_render_"))
    render_id = str(uuid.uuid4())[:8]
    
    try:
        # Write the code to a temporary file
        code_file = temp_dir / f"scene_{render_id}.py"
        code_file.write_text(code)
        
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location(f"scene_{render_id}", code_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"scene_{render_id}"] = module
        spec.loader.exec_module(module)
        
        # Find the scene class
        scene_class = find_scene_class(module, scene_name)
        
        # Get resolution for quality
        resolution = QUALITY_MAP.get(quality, QUALITY_MAP["medium"])
        file_extension = FORMAT_MAP.get(format, ".mp4")
        
        # Set up output directory
        output_dir = temp_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Configure camera
        camera_config = dict(
            resolution=resolution,
            fps=manim_config.camera.fps,
            background_color=manim_config.camera.background_color,
            background_opacity=manim_config.camera.background_opacity,
        )
        
        # Configure file writer
        file_writer_config = dict(
            write_to_movie=True,
            save_last_frame=False,
            movie_file_extension=file_extension,
            output_directory=str(output_dir),
            file_name=f"output_{render_id}",
            open_file_upon_completion=False,
            show_file_location_upon_completion=False,
            quiet=True,
            video_codec="libx264" if format == "mp4" else "",
            pixel_format="yuv420p" if format == "mp4" else "",
        )
        
        # Create and run the scene
        scene = scene_class(
            window=None,  # No window for headless rendering
            camera_config=camera_config,
            file_writer_config=file_writer_config,
            skip_animations=False,
            always_update_mobjects=False,
            show_animation_progress=False,
            leave_progress_bars=False,
        )
        
        scene.run()
        
        # Find the output video
        video_path = output_dir / f"output_{render_id}{file_extension}"
        
        if not video_path.exists():
            # Try to find any video file in the output directory
            video_files = list(output_dir.glob(f"*{file_extension}"))
            if video_files:
                video_path = video_files[0]
            else:
                raise FileNotFoundError(f"No video file generated in {output_dir}")
        
        return RenderResult(
            video_path=video_path,
            temp_dir=temp_dir,
            success=True
        )
        
    except Exception as e:
        return RenderResult(
            video_path=None,
            temp_dir=temp_dir,
            success=False,
            error=str(e)
        )
