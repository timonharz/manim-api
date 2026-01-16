"""
Render service for Manim animations.

This module handles the actual rendering of Manim code to video files by isolating execution in a subprocess.
"""

import tempfile
import uuid
import os
import sys
import importlib.util
import shutil
import contextlib
import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from addict import Dict

# Ensure manimlib is importable
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from manimlib.config import manim_config


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
    
    def __init__(self, video_path: Optional[Path], temp_dir: Optional[Path], success: bool, error: Optional[str] = None):
        self.video_path = video_path
        self.temp_dir = temp_dir
        self.success = success
        self.error = error
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)


def render_code(
    code: str,
    scene_name: Optional[str] = None,
    quality: str = "medium",
    format: str = "mp4",
    assets: Optional[dict[str, bytes]] = None
) -> RenderResult:
    """
    Render Manim code via a subprocess for memory isolation.
    """
    # Create temporary directory for this render
    temp_dir = Path(tempfile.mkdtemp(prefix="manim_render_"))
    render_id = str(uuid.uuid4())[:8]
    
    try:
        # Write assets if provided
        if assets:
            for filename, content in assets.items():
                (temp_dir / filename).write_bytes(content)

        # Write the code to a temporary file
        code_file = temp_dir / f"scene_{render_id}.py"
        code_file.write_text(code)
        
        # Validate the code
        try:
            compile(code, str(code_file), 'exec')
        except SyntaxError as e:
            raise ValueError(f"Generated code has syntax errors: {e}")
        
        # Check for hallucinations
        for bad in ['from manim import', 'import manim', 'from manif', 'import manif']:
            if bad in code:
                raise ValueError(f"Generated code contains illegal import '{bad}'. Regeneration needed.")
        
        # Resolve dimensions and paths
        resolution = QUALITY_MAP.get(quality, QUALITY_MAP["medium"])
        file_ext = FORMAT_MAP.get(format, ".mp4")
        output_dir = temp_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Prepare runner configuration
        config_path = temp_dir / "render_config.json"
        runner_config = {
            "code_path": str(code_file),
            "scene_name": scene_name,
            "camera_config": {
                "resolution": resolution,
                "fps": getattr(manim_config.camera, 'fps', 30),
                "background_color": str(getattr(manim_config.camera, 'background_color', 'BLACK')),
                "background_opacity": getattr(manim_config.camera, 'background_opacity', 1.0),
            },
            "file_writer_config": {
                "write_to_movie": True,
                "save_last_frame": False,
                "movie_file_extension": file_ext,
                "output_directory": str(output_dir),
                "file_name": f"output_{render_id}",
                "open_file_upon_completion": False,
                "show_file_location_upon_completion": False,
                "quiet": True,
                "video_codec": "libx264" if format == "mp4" else "",
                "pixel_format": "yuv420p" if format == "mp4" else "",
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(runner_config, f)
            
        # Run in subprocess
        runner_script = Path(__file__).parent / "manim_runner.py"
        process = subprocess.run(
            [sys.executable, str(runner_script), str(config_path)],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            raise RuntimeError(f"Rendering Process Error (Exit {process.returncode}):\n{process.stderr}\n{process.stdout}")
        
        # Find video path
        video_path = output_dir / f"output_{render_id}{file_ext}"
        if not video_path.exists():
            # Fallback search
            found = list(output_dir.glob(f"*{file_ext}"))
            if found:
                video_path = found[0]
            else:
                raise FileNotFoundError(f"Video file missing in {output_dir}. Output:\n{process.stdout}\n{process.stderr}")
        
        return RenderResult(video_path, temp_dir, True)
        
    except Exception as e:
        debug = f"CWD: {os.getcwd()}, Files: {os.listdir('.')[:10]}"
        return RenderResult(None, temp_dir, False, f"{str(e)} ({debug})")


# Service imports
from llm_service import LLMService
from tts_service import TTSService

class VideoGenerationService:
    def __init__(self):
        self.llm = LLMService()
        self.tts = TTSService()
    
    def generate_video(self, prompt: str, quality: str = "medium", format: str = "mp4", api_key: str = None) -> RenderResult:
        max_attempts = 2
        last_error = None
        
        for attempt in range(max_attempts):
            temp_audio_path = None
            try:
                eff_prompt = prompt
                if attempt > 0 and last_error:
                    eff_prompt = f"{prompt}\n\nFIX THIS ERROR: {last_error}. Strictly use manimlib."
                
                code, script = self.llm.generate_manim_content(eff_prompt, api_key=api_key)
                
                # Audio path
                temp_fd, temp_path_str = tempfile.mkstemp(suffix=".mp3")
                os.close(temp_fd)
                temp_audio_path = Path(temp_path_str)
                self.tts.generate_audio(script, temp_audio_path)
                
                # Render
                assets = {"narration.mp3": temp_audio_path.read_bytes()}
                result = render_code(code, quality=quality, format=format, assets=assets)
                
                if result.success:
                    return result
                
                last_error = result.error
                result.cleanup()
                    
            except Exception as e:
                last_error = str(e)
            finally:
                if temp_audio_path and temp_audio_path.exists():
                    os.unlink(temp_audio_path)
        
        return RenderResult(None, None, False, f"Generation failed after {max_attempts} attempts: {last_error}")
