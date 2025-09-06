# AI Video Generator - Application Flow

## High-Level Pipeline

The AI Video Generator follows a sophisticated pipeline that transforms a simple text topic into a complete video with narration, visuals, music, and captions. Here's the detailed flow:

## Phase 1: Content Generation

### 1.1 Script Generation (`generateVideoScript.py`)
**Input**: Topic (e.g., "benefits of eating mango")

**Process**:
- Determines if topic is a story or informational content
- Uses GPT-4 via Mindsflow agents to generate:
  - Structured script with sentences and timing
  - Image prompts for each scene
  - Music generation prompt
- Applies text style personalization if specified
- Saves script as JSON and uploads to S3

**Output**: 
- `json_string`: Raw script data
- `json_url`: S3 URL of structured script
- Individual script components (text, prompts, etc.)

### 1.2 Audio Generation Branch

#### 1.2.1 Narration (`textToSpeech.py`)
**Input**: Script text, language, speaker, voice speed

**Process**:
- Uses Azure Cognitive Services Text-to-Speech
- Supports multiple languages and voice styles
- Applies speed modifications using SSML
- Generates WAV audio file
- Calculates audio duration
- Uploads to S3

**Output**: 
- `audio_url`: S3 URL of narration
- `duration`: Audio length in seconds

#### 1.2.2 Background Music (`MusicGeneration.py`)
**Input**: Music prompt, duration, temperature, seed

**Process**:
- Uses Meta's MusicGen model via Replicate
- Generates music based on script-derived prompt
- Limits duration to maximum 28 seconds
- Returns direct URL to generated audio

**Output**:
- `music_url`: URL of generated background music

### 1.3 Visual Generation Branch

#### 1.3.1 Image-to-Video Generation (`PromptImagesToVideo.py`)
**Input**: Image prompts, video dimensions, timing JSON, style parameters

**Process**:
- Downloads timing JSON from script generation
- For each script sentence:
  - Generates contextual image prompt using LLM
  - Creates image using selected model (DALL-E 3, SDXL, etc.)
  - Applies cropping/resizing if needed
  - Creates video clip with zoom effects and transitions
- Concatenates all clips into single video
- Applies crossfade transitions between scenes
- Synchronizes timing with narration

**Output**:
- `video_url`: S3 URL of generated video
- `first_frame_url`: URL of thumbnail image

## Phase 2: Content Integration

### 2.1 Audio Mixing (`addSoundToVideo.py`)
**Input**: Video URL, narration URL, music URL, volume settings

**Process**:
- Downloads video and audio files
- Combines narration with background music
- Adjusts music volume relative to narration
- Handles audio repetition if needed
- Synchronizes audio length with video duration
- Exports as MP4 with AAC audio codec

**Output**:
- `video_url`: URL of video with combined audio

### 2.2 Caption Generation and Integration

#### 2.2.1 Subtitle Generation (`generateSrtFromJson.py`)
**Input**: Sentence timing JSON, minimum words per subtitle

**Process**:
- Downloads timing data from script generation
- Converts Azure time units to SRT format
- Combines short sentences based on punctuation and length
- Generates properly formatted SRT file
- Uploads to S3

**Output**:
- `srt_url`: URL of generated subtitle file

#### 2.2.2 Caption Integration (`AddCaptionsToVideoFFMPEG.py`)
**Input**: Video URL, SRT/ASS subtitle URL

**Process**:
- Downloads video and subtitle files
- Uses FFmpeg to burn captions into video
- Supports both SRT and ASS subtitle formats
- Handles subtitle positioning and styling
- Uploads final video to S3

**Output**:
- `video_url`: URL of video with embedded captions

## Phase 3: Post-Processing & Distribution

### 3.1 Final Assembly
The system creates a complete package containing:
- Final MP4 video file
- Thumbnail image
- Script text file  
- SRT subtitle file
- All packaged in a ZIP file

### 3.2 Upload and Distribution (`uploadYoutubeVideo.py`)
**Input**: Video URL, title, description, category, account credentials

**Process** (if upload enabled):
- Downloads final video
- Authenticates with YouTube API using stored credentials
- Uploads with specified metadata
- Returns upload status

**Output**:
- `upload_success`: Boolean indicating upload result

## Alternative Processing Paths

### Voice Cloning Pipeline
The system includes advanced voice cloning capabilities:

1. **Voice Training** (`voice_clone/voice_clone_api/train_api.py`)
   - Trains custom voice models from sample audio
   - Uses VITS (Variational Inference with adversarial learning for end-to-end Text-to-Speech)

2. **Voice Inference** (`voice_clone/voice_clone_api/infer_api.py`) 
   - Generates speech using trained voice models
   - Maintains voice characteristics and style

### Translation Pipeline
Multi-language support through translation modules:

1. **Content Translation** (`translateCaptionsJson.py`, `translateSrtFile.py`)
   - Translates scripts and captions to target languages
   - Preserves timing information

2. **Reverse Translation** (`translateTargetToSource.py`)
   - Enables bidirectional translation workflows

### Audio Processing Pipeline
Advanced audio manipulation capabilities:

1. **Audio Transcription** (`transcribeAudio.py`)
   - Converts speech to text with timestamps
   - Splits into sentence-level segments

2. **Audio Separation** (`splitVoiceMusic.py`)
   - Separates voice from background music
   - Enables audio track isolation

## Error Handling & Resilience

- **Retry Logic**: Image generation includes retry mechanisms
- **Fallback Models**: Multiple image generation models available
- **File Cleanup**: Temporary files are automatically cleaned up
- **AWS Integration**: Robust S3 upload/download with error handling

## Configuration Management

- **Environment Variables**: API keys and credentials stored securely
- **Parameter Validation**: Input parameters validated and defaulted
- **Model Selection**: Configurable AI models for different components

## Performance Optimizations

- **Parallel Processing**: Multiple components can run concurrently
- **Caching**: Generated content cached in S3
- **Resource Management**: Temporary files cleaned up promptly
- **Batch Processing**: Efficient handling of multiple assets

This comprehensive pipeline enables the transformation of a simple text topic into a polished, professional video suitable for social media platforms.