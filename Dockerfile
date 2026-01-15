
# Use python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for Manim and OpenGL
# ffmpeg: for video encoding
# build-essential: for compiling python packages
# libgl1-mesa-glx, libgl1-mesa-dev: for OpenGL
# libpango1.0-dev: for text rendering (manimpango)
# xauth, xvfb: for headless display (if needed, though we use OSMesa or offscreen)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libgl1-mesa-glx \
    libgl1-mesa-dev \
    libpango1.0-dev \
    libx11-6 \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables for headless rendering
# LIBGL_ALWAYS_SOFTWARE=1 forces software rendering if hardware is not available
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
