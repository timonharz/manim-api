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
import contextlib
from pathlib import Path
from typing import Optional
from addict import Dict

# Ensure manimlib is importable
sys.path.insert(0, str(Path(__file__).parent))

from manimlib.scene.scene import Scene
from manimlib.config import manim_config, load_yaml, get_manim_dir
from manimlib.utils.dict_ops import merge_dicts_recursively


@contextlib.contextmanager
def working_directory(path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


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
    format: str = "mp4",
    assets: Optional[dict[str, bytes]] = None
) -> RenderResult:
    """
    Render Manim code and return the path to the output video.
    
    Args:
        code: The Python code containing Manim scene definitions
        scene_name: Optional name of the specific scene to render
        quality: Video quality (low, medium, high, 4k)
        format: Output format (mp4, gif, mov)
        assets: Optional dict of filename -> bytes to write to the temp dir (e.g. audio files)
    
    Returns:
        RenderResult containing the path to the video and cleanup method
    """
    # Create temporary directory for this render
    temp_dir = Path(tempfile.mkdtemp(prefix="manim_render_"))
    render_id = str(uuid.uuid4())[:8]
    
    try:
        # Write assets if provided
        if assets:
            for filename, content in assets.items():
                asset_path = temp_dir / filename
                asset_path.write_bytes(content)

        # Write the code to a temporary file
        code_file = temp_dir / f"scene_{render_id}.py"
        code_file.write_text(code)
        
        # Validate the code before attempting to run it
        try:
            compile(code, code_file, 'exec')
        except SyntaxError as e:
            raise ValueError(f"Generated code has syntax errors: {e}")
        
        # Check for common hallucinations
        if 'from manim import' in code or 'import manim' in code:
            raise ValueError("Generated code uses 'manim' instead of 'manimlib'. Regeneration needed.")
        if 'from manif' in code or 'import manif' in code:
            raise ValueError("Generated code contains hallucinated module 'manif'. Regeneration needed.")
        
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
        
        # Create and run the scene in the temp directory so assets can be found
        with working_directory(temp_dir):
            # Diagnostic logging
            print(f"DEBUG: CWD set to {os.getcwd()}")
            print(f"DEBUG: Files in CWD: {os.listdir('.')}")
            
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
                files_listing = os.listdir(output_dir) if output_dir.exists() else "DIR_MISSING"
                raise FileNotFoundError(f"No video file generated in {output_dir}. Files: {files_listing}")
        
        return RenderResult(
            video_path=video_path,
            temp_dir=temp_dir,
            success=True
        )
        
    except Exception as e:
        debug_info = f"CWD: {os.getcwd()}, Files: {os.listdir('.')[:10]}"
        return RenderResult(
            video_path=None,
            temp_dir=temp_dir,
            success=False,
            error=f"{str(e)} ({debug_info})"
        )


# Service imports
from llm_service import LLMService
from tts_service import TTSService

class VideoGenerationService:
    def __init__(self):
        self.llm = LLMService()
        self.tts = TTSService()
    
    def generate_video(self, prompt: str, quality: str = "medium", format: str = "mp4", api_key: str = None) -> RenderResult:
        """
        Orchestrates the generation flow with retry logic:
        1. LLM generates code + script
        2. TTS generates audio (narration.mp3)
        3. render_code handles the rendering (with the code referencing narration.mp3)
        
        Retries once on failure with a refined prompt.
        """
        max_attempts = 2
        last_error = None
        
        for attempt in range(max_attempts):
            temp_audio_path = None
            try:
                # 1. Generate Content (with retry hint on subsequent attempts)
                effective_prompt = prompt
                if attempt > 0 and last_error:
                    effective_prompt = (
                        f"{prompt}\n\n"
                        f"CRITICAL: Your previous attempt failed with this error: '{last_error}'.\n"
                        f"PLEASE FIX IT. Remember to use ONLY `from manimlib import *`. "
                        f"Ensure all classes (Circle, Square, etc.) are available in manimlib."
                    )
                
                code, script = self.llm.generate_manim_content(effective_prompt, api_key=api_key)
                
                # 2. Generate Audio
                temp_fd, temp_path_str = tempfile.mkstemp(suffix=".mp3")
                os.close(temp_fd)
                temp_audio_path = Path(temp_path_str)
                
                self.tts.generate_audio(script, temp_audio_path)
                audio_bytes = temp_audio_path.read_bytes()
                
                # 3. Render Code with Audio Asset
                assets = {"narration.mp3": audio_bytes}
                
                result = render_code(
                    code=code,
                    quality=quality,
                    format=format,
                    assets=assets
                )
                
                if result.success:
                    return result
                else:
                    last_error = result.error
                    print(f"Attempt {attempt + 1} failed: {last_error}")
                    result.cleanup()
                    
            except Exception as e:
                # Catch LLM or TTS errors and retry
                last_error = str(e)
                print(f"Attempt {attempt + 1} exception: {last_error}")
            finally:
                # Cleanup local temp audio file
                if temp_audio_path and temp_audio_path.exists():
                    try:
                        os.unlink(temp_audio_path)
                    except:
                        pass
        
        # All attempts failed
        return RenderResult(None, None, False, f"Generation failed after {max_attempts} attempts: {last_error}")
