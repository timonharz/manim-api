# Build Version: 1.0.8
# Use python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for Manim and OpenGL
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libgl1 \
    libgl1-mesa-glx \
    libgl1-mesa-dev \
    libpango1.0-dev \
    libx11-6 \
    pkg-config \
    xvfb \
    libegl1-mesa-dev \
    libglib2.0-0 \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the application as a package (required for manimlib to find its version)
RUN pip install .

# Set environment variables for headless rendering
# LIBGL_ALWAYS_SOFTWARE=1 forces software rendering if hardware is not available
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV PYTHONUNBUFFERED=1

# Optimization for memory-constrained environments (512MB)
ENV MALLOC_ARENA_MAX=2

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--max-requests", "1000", "--max-requests-jitter", "50", "--bind", "0.0.0.0:8000", "--timeout", "300", "api:app"]
