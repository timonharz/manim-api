# Manim Video Streaming API Documentation

This API allows you to render Manim animations by either providing raw ManimGL code or using an AI prompt to generate the code and narration automatically.

## Base URL

The production API is hosted at:
`https://manim-api-production.up.railway.app`

For local development:
`http://localhost:8000`

---

## Endpoints

### 1. Root / Health Check

Check if the server is alive and get the current version.

- **URL**: `/` or `/health`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "status": "ALIVE_V1_1_11",
    "msg": "If you see this, v1.1.11 is live"
  }
  ```

### 2. Render Manim Code

Render a video from provided ManimGL code.

- **URL**: `/render`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "code": "string",          # Required: Valid python code using manimlib
    "scene_name": "string",   # Optional: Specific Scene class to render. If omitted, all scenes are rendered.
    "quality": "string",      # Optional: "low", "medium" (default), "high", "4k"
    "format": "string"        # Optional: "mp4" (default), "gif"
  }
  ```
- **Response**: Returns the generated video file as an attachment (`video/mp4`).
- **Error Response**: `400 Bad Request` if compilation or rendering fails.

### 3. Generate Video (AI Powered)

Generate an animation based on a natural language prompt. This endpoint uses an LLM to write the Manim code and a TTS service for the narration.

- **URL**: `/generate`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "prompt": "string",       # Required: Natural language description (e.g., "Explain the Pythagorean theorem")
    "api_key": "string",      # Required: Groq API Key
    "quality": "string",      # Optional: "low", "medium" (default), "high", "4k"
    "format": "string"        # Optional: "mp4" (default), "gif"
  }
  ```
- **Response**: Returns the generated video file containing both the animation and the AI-generated narration.

---

## Technical Details

### Multi-Scene Support

The server supports multiple `Scene` classes within a single request. If multiple scenes are detected, they are rendered sequentially and stitched together into a single final video using `ffmpeg`.

### Headless Rendering

The production environment uses `xvfb` (Virtual Framebuffer) and `Mesa` software rendering to generate videos without a physical GPU.

### LaTeX Support

Mathematical expressions are supported via `Tex`. In `manimlib` (ManimGL), `Tex` uses the `align*` environment by default, making it suitable for both multiline equations and single formulas.

---

## Client Examples

### Python (using `requests`)

```python
import requests

url = "https://manim-api-production.up.railway.app/render"
payload = {
    "code": "from manimlib import *\nclass Sample(Scene):\n    def construct(self):\n        self.add(Text('Hello World'))\n        self.wait(1)",
    "quality": "low"
}
response = requests.post(url, json=payload)

if response.status_code == 200:
    with open("animation.mp4", "wb") as f:
        f.write(response.content)
```
