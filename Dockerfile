# Build Version: 1.1.7
# Use python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for Manim and OpenGL
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libgl1 \
    libgl1-mesa-dev \
    libpango1.0-dev \
    libx11-6 \
    pkg-config \
    xvfb \
    libegl1-mesa-dev \
    libglib2.0-0 \
    libglu1-mesa \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the application as a package
RUN pip install .

# Set environment variables for headless rendering
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV PYTHONUNBUFFERED=1
ENV MALLOC_ARENA_MAX=2

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
