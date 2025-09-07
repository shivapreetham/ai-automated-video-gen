# How to Use the AI Video Generator

## Overview
This AI Video Generator creates engaging videos from text topics using AI-generated scripts, audio, and images. It runs as a Flask backend server with a complete workflow pipeline.

## Setup & Running

### Start the Backend Server
```bash
python app.py
```
The server will start on `http://localhost:8001`

### Frontend Interface
Visit `http://localhost:8001` in your browser for the web interface, or use the API directly.

## API Usage

### 1. Generate Video (POST /generate-video)

**Basic Request:**
```bash
curl -X POST http://localhost:8001/generate-video \
  -H "Content-Type: application/json" \
  -d '{"topic": "space exploration"}'
```

**Full Parameters:**
```bash
curl -X POST http://localhost:8001/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "underground living humans",
    "width": 1920,
    "height": 1080,
    "script_size": "long"
  }'
```

**Parameters:**
- `topic` (required): The video topic/subject
- `width` (optional): Video width in pixels (256-2048, default: 1024)
- `height` (optional): Video height in pixels (256-2048, default: 576)  
- `script_size` (optional): Script length - "short", "medium", "long" (default: "medium")

**Response:**
```json
{
  "success": true,
  "job_id": "12345-uuid-67890",
  "status": "queued",
  "message": "Video generation started",
  "check_status": "/jobs/12345-uuid-67890/status"
}
```

### 2. Check Job Status (GET /jobs/{job_id}/status)

```bash
curl http://localhost:8001/jobs/12345-uuid-67890/status
```

**Response:**
```json
{
  "job_id": "12345-uuid-67890",
  "status": "processing",
  "progress": 60,
  "message": "Generating images with Pollinations AI...",
  "current_step": "Image Generation",
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:02:30"
}
```

**Status Values:**
- `queued`: Job waiting to start
- `processing`: Currently generating video
- `completed`: Video ready for download
- `failed`: Error occurred

### 3. Download Completed Video (GET /jobs/{job_id}/download)

```bash
curl -O http://localhost:8001/jobs/12345-uuid-67890/download
```

### 4. List All Job Files (GET /jobs/{job_id}/files)

```bash
curl http://localhost:8001/jobs/12345-uuid-67890/files
```

**Response:**
```json
{
  "job_id": "12345-uuid-67890",
  "files": {
    "video": "results/12345-uuid-67890/final_video.mp4",
    "audio": "results/12345-uuid-67890/audio.wav",
    "script": "results/12345-uuid-67890/script.txt",
    "images": ["results/12345-uuid-67890/image_0.png", "..."],
    "job_folder": "results/12345-uuid-67890"
  }
}
```

### 5. List All Jobs (GET /jobs)

```bash
curl http://localhost:8001/jobs
```

### 6. Cleanup All Data (POST /cleanup)

```bash
curl -X POST http://localhost:8001/cleanup
```

## Video Generation Workflow

The system follows this pipeline:

1. **Script Generation** - Gemini AI creates segments based on topic and script_size
2. **Audio Generation** - ElevenLabs converts script to speech with realistic voice
3. **Image Generation** - Pollinations AI creates visuals for each script segment
4. **Video Assembly** - FFmpeg combines images and audio into final video

## File Organization

All outputs are organized by job ID:
```
results/
├── {job_id_1}/
│   ├── final_video.mp4
│   ├── audio.wav
│   ├── script.txt
│   └── image_0.png, image_1.png, ...
└── {job_id_2}/
    └── ...
```

## Example Workflow

```bash
# 1. Start video generation
RESPONSE=$(curl -s -X POST http://localhost:8001/generate-video \
  -H "Content-Type: application/json" \
  -d '{"topic": "ancient civilizations", "script_size": "medium"}')

# 2. Extract job ID
JOB_ID=$(echo $RESPONSE | jq -r '.job_id')

# 3. Monitor progress
while true; do
  STATUS=$(curl -s http://localhost:8001/jobs/$JOB_ID/status | jq -r '.status')
  if [ "$STATUS" = "completed" ]; then
    echo "Video ready!"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Generation failed"
    break
  else
    echo "Status: $STATUS"
    sleep 10
  fi
done

# 4. Download video
curl -O http://localhost:8001/jobs/$JOB_ID/download
```

## Tips

- Use descriptive topics for better results: "medieval castle life" vs "castles"
- Longer script sizes create more detailed videos but take more time
- Monitor job status regularly - processing can take 2-10 minutes
- All files persist until manual cleanup via `/cleanup` endpoint
- The system handles job queuing automatically for concurrent requests