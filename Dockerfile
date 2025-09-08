FROM python:3.9-slim-buster

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    PORT=8000 \
    FLASK_ENV=production \
    DEBIAN_FRONTEND=noninteractive

# System dependencies - using older base image that works reliably
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
        libfontconfig1 \
        libxrender1 \
        libgl1-mesa-glx \
        libglib2.0-0 \
        curl \
        wget \
        ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py ./
COPY backend_functions/ ./backend_functions/
COPY satirical_agent/ ./satirical_agent/

# Create directories and set permissions
RUN mkdir -p results temp static logs data && \
    groupadd -r appuser && \
    useradd -r -g appuser -d /app appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "2", \
    "--threads", "2", \
    "--timeout", "600", \
    "app:app"]
