# AI Video Generator Backend Dockerfile
# Optimized for Akash Network deployment

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV FLASK_APP=app.py
ENV PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    gcc \
    g++ \
    cmake \
    pkg-config \
    wget \
    curl \
    git \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libasound2-dev \
    portaudio19-dev \
    espeak \
    espeak-data \
    libopencv-dev \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements_docker.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements_docker.txt

# Copy application files
COPY app.py .
COPY backend_functions/ ./backend_functions/
COPY integrated_daily_mash_system.py .
COPY .env .

# Copy old_functions directory if it exists (for fallbacks)
COPY old_functions/ ./old_functions/

# Create necessary directories
RUN mkdir -p /app/results /app/temp /app/static /app/logs

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--worker-class", "gthread", "--timeout", "300", "--keep-alive", "60", "app:app"]