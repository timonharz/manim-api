"""
Manim Video Streaming REST API (Resilient Async Version)
"""

import os
import asyncio
import traceback
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

import fastapi
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from render_service import render_code, RenderResult, VideoGenerationService

# Store active render results for cleanup
_active_renders: dict[str, RenderResult] = {}
_render_semaphore: Optional[asyncio.Semaphore] = None

def get_render_semaphore():
    global _render_semaphore
    if _render_semaphore is None:
        _render_semaphore = asyncio.Semaphore(1)
    return _render_semaphore

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

# Robust Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = str(exc)
    print(f"Unhandled exception: {error_detail}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": f"Internal server error: {error_detail}"})

class RenderRequest(BaseModel):
    code: str
    scene_name: Optional[str] = None
    quality: str = "medium"
    format: str = "mp4"

@app.get("/")
async def root():
    return {"name": "Manim Video Streaming API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "manim-api"}

@app.post("/ping")
async def ping():
    return {"message": "pong"}

@app.post("/render", response_class=FileResponse)
async def render_animation(request: RenderRequest, background_tasks: BackgroundTasks):
    async with get_render_semaphore():
        result = await run_in_threadpool(
            render_code,
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
    async with get_render_semaphore():
        result = await run_in_threadpool(
            video_gen_service.generate_video,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
