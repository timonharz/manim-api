# Build Version: 1.2.1
# Optimized for Railway.app (under 4GB image size)
# Multi-stage build with minimal TeX Live

# Stage 1: Build stage
FROM python:3.10-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    pkg-config \
    libpango1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install python dependencies to a specific location
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime stage (minimal)
FROM python:3.10-slim-bookworm

WORKDIR /app

# Install runtime dependencies with minimal TeX Live
# We combine install and cleanup in one layer to keep the image small (< 4GB)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libpango1.0-0 \
    libx11-6 \
    libxrender1 \
    libxext6 \
    xvfb \
    libegl1-mesa \
    libglib2.0-0 \
    libglu1-mesa \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-humanities \
    texlive-science \
    tipa \
    dvipng \
    dvisvgm \
    xauth \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/* \
    && rm -rf /usr/share/doc/* \
    && rm -rf /usr/share/man/* \
    && rm -rf /usr/share/texlive/texmf-dist/doc \
    && rm -rf /usr/share/texlive/texmf-dist/source \
    && rm -rf /usr/share/texlive/texmf-dist/tex/latex/base/README* \
    && find /usr/share/texlive -type f -name "*.pdf" -delete

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Install the application as a package
RUN pip install --no-cache-dir .

# Set environment variables for headless rendering
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV PYTHONUNBUFFERED=1
ENV MALLOC_ARENA_MAX=2

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
