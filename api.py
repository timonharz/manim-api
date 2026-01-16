"""
Manim Video Streaming REST API

A FastAPI application that accepts Manim animation code and returns the rendered video.
"""

import os
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from render_service import render_code, RenderResult


# Store active render results for cleanup
_active_renders: dict[str, RenderResult] = {}


def cleanup_render(render_id: str):
    """Background task to clean up render files."""
    if render_id in _active_renders:
        _active_renders[render_id].cleanup()
        del _active_renders[render_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    yield
    # Cleanup any remaining renders on shutdown
    for render_id, result in _active_renders.items():
        result.cleanup()
    _active_renders.clear()


app = FastAPI(
    title="Manim Video Streaming API",
    description="Submit Manim animation code and receive the rendered video",
    version="1.0.0",
    lifespan=lifespan,
)


# Exception handlers to prevent 502 errors and provide clean JSON responses
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return a proper JSON response."""
    error_detail = str(exc)
    print(f"Unhandled exception: {error_detail}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {error_detail}"}
    )



class RenderRequest(BaseModel):
    """Request body for rendering a Manim animation."""
    
    code: str = Field(
        ...,
        description="Python code containing Manim scene definition",
        examples=[
            """from manimlib import *

class CircleAnimation(Scene):
    def construct(self):
        circle = Circle()
        circle.set_fill(BLUE, opacity=0.5)
        self.play(ShowCreation(circle))
        self.wait()
"""
        ]
    )
    scene_name: Optional[str] = Field(
        None,
        description="Name of the scene class to render. If not provided, the last defined scene will be used."
    )
    quality: str = Field(
        "medium",
        description="Video quality: 'low' (480p), 'medium' (720p), 'high' (1080p), '4k' (2160p)",
        pattern="^(low|medium|high|4k)$"
    )
    format: str = Field(
        "mp4",
        description="Output format: 'mp4', 'gif', or 'mov'",
        pattern="^(mp4|gif|mov)$"
    )


class RenderResponse(BaseModel):
    """Response for successful render."""
    success: bool
    message: str


class ErrorResponse(BaseModel):
    """Response for render errors."""
    success: bool = False
    error: str


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "manim-video-streaming-api"}


@app.post(
    "/render",
    response_class=FileResponse,
    responses={
        200: {
            "content": {"video/mp4": {}, "image/gif": {}, "video/quicktime": {}},
            "description": "Rendered video file"
        },
        400: {"model": ErrorResponse, "description": "Invalid request or render error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def render_animation(request: RenderRequest, background_tasks: BackgroundTasks):
    """
    Render a Manim animation and return the video.
    
    Submit Python code containing a Manim Scene definition, and receive
    the rendered video as a file download.
    
    **Example code:**
    ```python
    from manimlib import *
    
    class MyScene(Scene):
        def construct(self):
            circle = Circle()
            self.play(ShowCreation(circle))
            self.wait()
    ```
    """
    try:
        # Render the animation
        result = render_code(
            code=request.code,
            scene_name=request.scene_name,
            quality=request.quality,
            format=request.format
        )
        
        if not result.success:
            # Clean up on error
            result.cleanup()
            raise HTTPException(status_code=400, detail=f"Render failed: {result.error}")
        
        if not result.video_path or not result.video_path.exists():
            result.cleanup()
            raise HTTPException(status_code=500, detail="Video file was not generated")
        
        # Store for cleanup
        render_id = str(result.video_path.stem)
        _active_renders[render_id] = result
        
        # Schedule cleanup after response is sent
        background_tasks.add_task(cleanup_render, render_id)
        
        # Determine media type
        media_types = {
            ".mp4": "video/mp4",
            ".gif": "image/gif",
            ".mov": "video/quicktime",
        }
        suffix = result.video_path.suffix.lower()
        media_type = media_types.get(suffix, "application/octet-stream")
        
        # Return the video file
        return FileResponse(
            path=str(result.video_path),
            media_type=media_type,
            filename=f"animation{suffix}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Manim Video Streaming API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "POST /render": "Submit Manim code and receive rendered video",
            "POST /generate": "Generate video from prompt (LLM + TTS)"
        }
    }


# Service instantiation
from render_service import VideoGenerationService
video_gen_service = VideoGenerationService()


class GenerateRequest(BaseModel):
    """Request body for generating a video from prompt."""
    prompt: str = Field(..., description="Prompt describing the video content and narration.")
    quality: str = Field("medium", description="Video quality (low, medium, high, 4k)")
    format: str = Field("mp4", description="Output format (mp4, gif, mov)")
    api_key: Optional[str] = Field(None, description="Groq API Key (overrides server-side key)")


@app.post(
    "/generate",
    response_class=FileResponse,
    description="Generate a narrated video from a text prompt using Groq + gTTS."
)
async def generate_video_endpoint(request: GenerateRequest, background_tasks: BackgroundTasks):
    if not video_gen_service:
         raise HTTPException(status_code=500, detail="Generation service not available (missing dependencies?)")

    try:
        result = video_gen_service.generate_video(
            prompt=request.prompt, 
            quality=request.quality, 
            format=request.format,
            api_key=request.api_key
        )
        
        if not result.success:
            result.cleanup()
            raise HTTPException(status_code=400, detail=result.error)
            
        if not result.video_path or not result.video_path.exists():
            result.cleanup()
            raise HTTPException(status_code=500, detail="Video file was not generated")

        # Store for cleanup
        render_id = str(result.video_path.stem)
        _active_renders[render_id] = result
        
        background_tasks.add_task(cleanup_render, render_id)
        
        # Determine media type (duplicated logic, could be helper)
        media_types = {".mp4": "video/mp4", ".gif": "image/gif", ".mov": "video/quicktime"}
        suffix = result.video_path.suffix.lower()
        media_type = media_types.get(suffix, "application/octet-stream")
        
        return FileResponse(
            path=str(result.video_path),
            media_type=media_type,
            filename=f"generated_video{suffix}"
        )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
