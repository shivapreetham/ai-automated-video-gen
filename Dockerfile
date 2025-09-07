FROM python:3.12-slim

# Runtime environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    FLASK_APP=app.py \
    PORT=8000

# System dependencies (minimal, for OpenCV, ffmpeg, SciPy/Numpy, healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# Copy application code
COPY app.py ./
COPY backend_functions ./backend_functions
COPY agents ./agents
COPY integrated_daily_mash_system.py ./
COPY content_generator_integration.py ./

# Create necessary directories
RUN mkdir -p /app/results /app/temp /app/static /app/logs

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser \
  && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run via gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--worker-class", "gthread", "--timeout", "300", "--keep-alive", "60", "app:app"]
