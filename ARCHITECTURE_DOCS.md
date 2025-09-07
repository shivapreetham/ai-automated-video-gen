# AI Video Generator - Architecture Documentation

## Overview

The AI Video Generator has been enhanced with a new **Story Mode** that creates engaging, narrative-driven videos with proper audio-visual synchronization. The system now supports two modes:

1. **Legacy Mode**: Simple video generation (existing system)
2. **Story Mode**: Advanced story-driven video generation with characters, dialogs, and proper sync

## System Architecture

### Flask Application (`app.py`)

The Flask application serves as the main API endpoint and job orchestrator.

#### Key Features:
- **Dual Mode Support**: Both legacy and story modes
- **Job Management**: Asynchronous video generation with progress tracking
- **RESTful API**: Clean endpoints for video generation and monitoring
- **Background Processing**: Non-blocking video generation using threads

#### API Endpoints:

```
GET  /                    - Homepage/Frontend
GET  /api                 - API information and documentation
POST /generate-video      - Start video generation
GET  /jobs/<id>/status    - Check job progress
GET  /jobs/<id>/download  - Download completed video
GET  /jobs/<id>/files     - List all job files
GET  /jobs                - List all active jobs
POST /cleanup             - Clean up job data
GET  /system-check        - Validate system requirements
```

#### Video Generation Parameters:

**Required:**
- `topic` (string): Main topic/theme for the story

**Optional:**
- `width` (int, default: 1024): Video width
- `height` (int, default: 576): Video height
- `script_length` (string, default: "medium"): "short", "medium", or "long"
- `voice` (string, default: "alloy"): "nova", "alloy", "echo", or "fable"
- `img_style_prompt` (string, default: "cinematic, professional"): Image style
- `story_mode` (bool, default: false): Use new story system
- `include_dialogs` (bool, default: true): Include character dialogs
- `use_different_voices` (bool, default: true): Different voices for characters
- `add_captions` (bool, default: true): Add subtitle overlay

### Backend Functions Architecture

Located in the `backend_functions/` directory, these modules handle the core video generation pipeline.

## Story Mode Pipeline (New System)

### 1. Story Script Generator (`story_script_generator.py`)

**Purpose**: Creates engaging story scripts with characters, dialogs, and narrative structure.

**Key Features:**
- Character development with distinct personalities
- Variable-length segments based on story pacing
- Dialog integration with character voices
- Cinematic scene descriptions
- Story arc structure (beginning, development, climax, resolution)

**Output**: JSON with story metadata, characters, and detailed segments

**Example Usage:**
```python
from backend_functions.story_script_generator import generate_story_script

result = generate_story_script(
    topic="cat and dog friendship",
    script_length="medium",
    include_dialogs=True
)
```

### 2. Segment Audio Generator (`segment_audio_generator.py`)

**Purpose**: Generates individual audio files for each story segment with proper voice assignment.

**Key Features:**
- Per-segment audio generation
- Character voice mapping (different voices for different characters)
- Emotional tone adjustment based on scene type
- Concurrent processing for speed
- ElevenLabs API with gTTS fallback

**Voice Assignment:**
- Narrator: Primary voice
- Characters: Different voices based on character roles
- Dialog vs Narrative: Different voice settings for better expression

**Output**: Individual audio files with accurate duration metadata

### 3. Segment Image Generator (`segment_image_generator.py`)

**Purpose**: Creates contextually appropriate images for each story segment.

**Key Features:**
- Multiple images per segment (1-3 based on content)
- Context-aware prompt enhancement
- Emotional tone integration
- Concurrent image generation
- Pollinations AI integration

**Image Enhancement:**
- Base prompt + visual theme + style prompt + emotional modifiers
- Technical quality markers added automatically
- Segment type considerations (narrative vs dialog framing)

### 4. Segment Video Creator (`segment_video_creator.py`)

**Purpose**: Creates individual video clips for each segment with perfect audio-visual sync.

**Key Features:**
- Per-segment video creation
- Proper audio-visual synchronization
- Multiple images per segment with smooth transitions
- MoviePy preferred, FFmpeg fallback
- Variable segment durations based on actual audio length

**Sync Strategy:**
- Audio duration determines final video length
- Images are timed proportionally within each segment
- Crossfade transitions between images
- No forced timing constraints

### 5. Video Segment Stitcher (`video_segment_stitcher.py`)

**Purpose**: Combines individual segment videos into a cohesive final story.

**Key Features:**
- Seamless segment transitions
- Title and end cards
- Comprehensive caption system
- Professional video output
- Story continuity preservation

**Stitching Process:**
1. Optional title card with story title
2. Segment videos with smooth transitions
3. Optional end card
4. Caption overlay with proper timing
5. Final quality optimization

### 6. Story Video Generator (`story_video_generator.py`)

**Purpose**: Main orchestrator that coordinates all story generation components.

**Workflow:**
1. **Script Generation**: Create story with characters and structure
2. **Audio Generation**: Generate per-segment audio with voice variety
3. **Image Generation**: Create contextual images for each segment
4. **Video Creation**: Build individual segment videos with sync
5. **Final Stitching**: Combine into cohesive story with captions

## Legacy Mode Pipeline (Existing System)

Uses the existing `video_generator.py` with backend functions:
- `gemini_script.py`: Basic script generation
- `elevenlabs_audio.py`: Single audio file generation
- `pollinations_images.py`: Image generation
- `ffmpeg_video.py`: Video creation

## Job Management System

### Job States:
- `queued`: Job created, waiting to start
- `processing`: Video generation in progress
- `completed`: Video successfully generated
- `failed`: Generation failed with error

### Job Data Structure:
```python
{
    "job_id": "unique_identifier",
    "status": "completed",
    "progress": 100,
    "message": "Video generation completed successfully",
    "current_step": "Completed",
    "created_at": "2025-01-07T12:00:00",
    "updated_at": "2025-01-07T12:05:00",
    "result": {
        "video_file": "/path/to/final_video.mp4",
        "story_title": "The Great Adventure",
        "total_segments": 6,
        "processing_time": 245.3,
        "mode": "story"
    }
}
```

## File Organization

### Results Directory Structure:
```
results/
├── {job_id}/
│   ├── story_script.json          # Generated story script
│   ├── audio_results.json         # Audio generation results
│   ├── image_results.json         # Image generation results
│   ├── segment_video_results.json # Segment video results
│   ├── final_video_results.json   # Final video metadata
│   ├── complete_generation_results.json # Complete process log
│   ├── segment_01_audio_*.mp3     # Individual audio files
│   ├── seg_01_img_01_*.jpg        # Individual images
│   ├── segment_01_video_*.mp4     # Individual segment videos
│   ├── Story_Title_*.mp4          # Final story video
│   └── story_captions.srt         # Subtitle file
```

## System Requirements

### Required:
- **Python 3.8+**
- **FFmpeg** (via imageio-ffmpeg or system installation)
- **Flask** for API server
- **Internet connection** for AI services

### Optional (Recommended):
- **MoviePy** for advanced video processing
- **gTTS** for audio fallback

### AI Services:
- **Gemini AI** for script generation
- **ElevenLabs** for premium audio (with gTTS fallback)
- **Pollinations AI** for image generation

## Configuration

### API Keys Required:
- `GEMINI_API_KEY`: For script generation
- `ELEVENLABS_API_KEY`: For premium audio generation

### Voice Options:
- `nova`: Male voice, clear and professional
- `alloy`: Balanced, versatile voice (default)
- `echo`: Warm, friendly voice
- `fable`: Expressive, story-telling voice

## Performance Considerations

### Story Mode Optimizations:
- **Concurrent Processing**: Audio and image generation run in parallel
- **Efficient Memory Usage**: Segments processed individually
- **Smart Caching**: Reuse of generated assets when possible
- **Error Recovery**: Graceful fallback for failed components

### Typical Generation Times:
- **Short Story** (3-4 segments): 2-4 minutes
- **Medium Story** (5-7 segments): 4-8 minutes  
- **Long Story** (8-12 segments): 8-15 minutes

*Times vary based on internet connection and AI service response times.*

## Error Handling

The system includes comprehensive error handling:
- **Graceful Degradation**: Falls back to simpler methods when advanced features fail
- **Detailed Logging**: All steps logged for debugging
- **Partial Success**: Continues with available components even if some fail
- **User Feedback**: Clear error messages with actionable suggestions

## Testing

### System Validation:
```bash
curl http://localhost:8001/system-check
```

### Story Generation Test:
```bash
curl -X POST http://localhost:8001/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "cat and dog friendship",
    "story_mode": true,
    "script_length": "medium",
    "include_dialogs": true
  }'
```

## Conclusion

The new Story Mode represents a significant advancement in automated video generation, providing:
- **Engaging Narratives**: Character-driven stories with emotional depth
- **Perfect Synchronization**: Audio and visuals perfectly timed
- **Professional Quality**: Cinematic transitions and captions
- **Scalable Architecture**: Easy to extend and maintain

The dual-mode system ensures backward compatibility while offering advanced storytelling capabilities for users who want more sophisticated video content.