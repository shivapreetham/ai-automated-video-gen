# AI Video Generator Documentation

## Overview

This is an AI-powered video generation system that automatically creates short videos from text topics and posts them on social platforms. The system integrates multiple AI domains including script generation, image generation, music generation, speech synthesis, automatic captioning, and video composition.

## Project Structure

```
ai-video-generator/
├── agent-video-generator/functions/    # Main video generation functions
├── voice_clone/                       # Voice cloning functionality 
├── results/                           # Sample outputs and flow diagrams
└── docs/                             # Documentation (this folder)
```

## Core Components

### 1. Script Generation Module
- **File**: `generateVideoScript.py`
- **Purpose**: Generates video scripts using GPT-4 based on topic input
- **Key Features**:
  - Story vs paragraph generation based on topic keywords
  - Music prompt generation
  - Text style personalization
  - Integration with Mindsflow AI agents

### 2. Image Generation Module
- **File**: `PromptImagesToVideo.py`
- **Purpose**: Creates video from AI-generated images
- **Key Features**:
  - Multiple image generation models (DALL-E 3, Stable Diffusion XL, etc.)
  - Dynamic prompt generation from script sentences
  - Video transitions and zoom effects
  - Frame synchronization with audio timing

### 3. Audio Generation Modules

#### Text-to-Speech
- **File**: `textToSpeech.py`
- **Purpose**: Converts text to speech using Azure Cognitive Services
- **Features**: Multiple languages, voice speeds, speaker selection

#### Music Generation  
- **File**: `MusicGeneration.py`
- **Purpose**: Creates background music using Meta's MusicGen model
- **Features**: Customizable duration, temperature, and seed parameters

#### Voice Cloning
- **Files**: `cloneVoiceValleX.py`, `cloneVoiceVits.py`, `generateVoiceVits.py`
- **Purpose**: Clone voices and generate speech with cloned voices

### 4. Video Composition Modules

#### Captions Integration
- **Files**: 
  - `AddCaptionsToVideoFFMPEG.py` - FFMPEG-based caption overlay
  - `AddCaptionsToVideoMoviepy.py` - MoviePy-based caption overlay  
  - `AddCaptionsToVideoOpenCV.py` - OpenCV-based caption overlay
  - `generateSrtFromJson.py` - SRT file generation from JSON timestamps

#### Audio-Video Synchronization
- **File**: `addSoundToVideo.py`
- **Purpose**: Combines audio (narration + music) with video
- **Features**: Volume control, audio repetition, audio mixing

### 5. Content Processing Modules

#### Translation
- **Files**: 
  - `translateSrtFile.py` - Translate SRT subtitle files
  - `translateCaptionsJson.py` - Translate JSON caption data
  - `translateTargetToSource.py` - Bidirectional translation

#### Audio Processing
- **Files**:
  - `transcribeAudio.py` - Audio-to-text transcription
  - `AudioTranscriptionToSentences.py` - Split transcription into timed sentences
  - `splitVoiceMusic.py` - Separate voice from background music
  - `generateAudioSegmentsFromJson.py` - Create audio segments from JSON data
  - `addAudioSegmentsToVideo.py` - Add segmented audio to video

### 6. Utility Modules

#### File Management
- **Files**:
  - `deleteFilesByExtension.py` - Clean up files by extension
  - `deleteFolders.py` - Remove directories
  - `UploadResultZipS3.py` - Upload final results to S3

#### Configuration & Data
- **Files**:
  - `loadJsonAndReturnKeys.py` - JSON data extraction
  - `returnInputParameters.py` - Parameter validation
  - `setEpochInJsonFile.py` - Training epoch configuration
  - `ShowFonts.py` - Font management for captions

#### Platform Integration
- **Files**:
  - `uploadYoutubeVideo.py` - YouTube video upload
  - `CommandsExecution.py` - System command execution
  - `MindsflowAgent.py` - Mindsflow platform integration

### 7. Voice Clone API System
Located in `voice_clone/voice_clone_api/`:
- **`train_api.py`** - Voice model training API
- **`infer_api.py`** - Voice inference API  
- **`functions.py`** - Core voice cloning functions
- **`infer.py`** - Inference engine
- **`train.py`** - Training engine

## Technology Stack

### AI/ML Services
- **OpenAI GPT-4** - Script generation
- **DALL-E 3** - Image generation
- **Stable Diffusion XL** - Image generation  
- **Meta MusicGen** - Music generation
- **Azure Cognitive Services** - Text-to-speech
- **Replicate** - AI model hosting

### Media Processing
- **FFmpeg** - Video/audio processing
- **MoviePy** - Python video editing
- **OpenCV** - Computer vision operations
- **PIL (Pillow)** - Image processing
- **PyDub** - Audio manipulation

### Cloud Services
- **AWS S3** - File storage and hosting
- **Mindsflow.ai** - AI agent orchestration

### Development
- **Python** - Primary programming language
- **Boto3** - AWS SDK
- **Requests** - HTTP client

## Input/Output Format

### Input
```json
{
    "topic": "topic of the video",
    "language": "en", 
    "speaker": "en-US-GuyNeural",
    "voice_speed": 1,
    "font_size": 30,
    "height": 1024,
    "width": 576,
    "fps": 16,
    "image_model": "sdxl",
    "music_volume": 0.5,
    "upload": false
}
```

### Output
```json
{
    "result": "link to ZIP file containing video, thumbnail, script, and captions"
}
```

## Next Steps

Refer to the following documentation files for detailed information:
- `application-flow.md` - Detailed application flow and pipeline
- `visual-pipeline.md` - Visual representation of the video generation pipeline
- `file-reference.md` - Complete file-by-file breakdown