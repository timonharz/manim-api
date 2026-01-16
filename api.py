"""
Manim Video Streaming REST API (Minimal Stable Version)
"""

import os
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from render_service import render_code, RenderResult, VideoGenerationService

# Store active render results for cleanup
_active_renders: dict[str, RenderResult] = {}

def cleanup_render(render_id: str):
    """Background task to clean up render files."""
    if render_id in _active_renders:
        _active_renders[render_id].cleanup()
        del _active_renders[render_id]

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    for render_id, result in _active_renders.items():
        result.cleanup()
    _active_renders.clear()

app = FastAPI(
    title="Manim Video Streaming API",
    version="1.0.0",
    lifespan=lifespan,
)

class RenderRequest(BaseModel):
    code: str
    scene_name: Optional[str] = None
    quality: str = "medium"
    format: str = "mp4"

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "manim-api"}

@app.post("/render", response_class=FileResponse)
async def render_animation(request: RenderRequest, background_tasks: BackgroundTasks):
    result = render_code(
        code=request.code,
        scene_name=request.scene_name,
        quality=request.quality,
        format=request.format
    )
    
    if not result.success:
        result.cleanup()
        raise HTTPException(status_code=400, detail=result.error)
    
    render_id = str(result.video_path.stem)
    _active_renders[render_id] = result
    background_tasks.add_task(cleanup_render, render_id)
    
    return FileResponse(path=str(result.video_path), filename=f"animation{result.video_path.suffix}")

# AI Generation
video_gen_service = VideoGenerationService()

class GenerateRequest(BaseModel):
    prompt: str
    quality: str = "medium"
    format: str = "mp4"
    api_key: Optional[str] = None

@app.post("/generate", response_class=FileResponse)
async def generate_video_endpoint(request: GenerateRequest, background_tasks: BackgroundTasks):
    result = video_gen_service.generate_video(
        prompt=request.prompt,
        quality=request.quality,
        format=request.format,
        api_key=request.api_key
    )
    
    if not result.success:
        result.cleanup()
        raise HTTPException(status_code=400, detail=result.error)
        
    render_id = str(result.video_path.stem)
    _active_renders[render_id] = result
    background_tasks.add_task(cleanup_render, render_id)
    
    return FileResponse(path=str(result.video_path), filename=f"video{result.video_path.suffix}")
