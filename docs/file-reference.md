# AI Video Generator - Complete File Reference

## 📁 Project Structure Overview

```
ai-video-generator/
├── 📂 agent-video-generator/functions/    # Main video generation pipeline
├── 📂 voice_clone/                       # Voice cloning system
├── 📂 results/                           # Sample outputs and flow diagrams  
├── 📂 docs/                              # Documentation (this folder)
├── 📂 venv/                              # Virtual environment
├── 📄 requirements.txt                   # Python dependencies
└── 📄 README.md                          # Project overview
```

---

## 🎬 Core Video Generation Functions
*Location: `agent-video-generator/functions/`*

### 📝 Content Generation

#### `generateVideoScript.py` 
**Purpose**: Main script generation using GPT-4
- **Function**: `mindsflow_function(event, context)`
- **Input**: Topic string, text style (optional)
- **Output**: Structured script JSON with image prompts and music prompt
- **AI Models**: GPT-4 via Mindsflow agents (1601, 1599, 1604, 1548)
- **Key Features**:
  - Detects story vs informational content
  - Generates contextual image prompts
  - Creates music generation prompts
  - Applies text style transformations
  - Uploads script JSON to S3

#### `PromptImagesToVideo.py`
**Purpose**: Converts image prompts into complete video
- **Function**: `mindsflow_function(event, context)`
- **Input**: Image prompts, video dimensions, timing data
- **Output**: Silent MP4 video with transitions
- **AI Models**: DALL-E 3, Stable Diffusion XL, Playground, Kandinsky
- **Key Features**:
  - Multi-model image generation with fallbacks
  - Dynamic prompt enhancement using LLM
  - Video assembly with crossfade transitions
  - Zoom effects and motion
  - Frame-by-frame timing synchronization
  - S3 integration for asset storage

---

### 🎵 Audio Generation

#### `textToSpeech.py`
**Purpose**: Text-to-speech narration generation
- **Function**: `mindsflow_function(event, context)`
- **Input**: Text, language, speaker, voice speed
- **Output**: WAV audio file with duration
- **Technology**: Azure Cognitive Services Speech SDK
- **Key Features**:
  - Multi-language support (EN, CH, IT, DE, FR, ES)
  - Voice speed control with SSML
  - Duration calculation
  - Azure speaker selection
  - S3 upload and URL generation

#### `MusicGeneration.py`
**Purpose**: Background music generation
- **Function**: `mindsflow_function(event, context)`
- **Input**: Music prompt, duration, temperature, seed
- **Output**: Generated music audio URL
- **AI Model**: Meta MusicGen (Large model)
- **Key Features**:
  - Customizable music generation
  - Duration limits (max 28 seconds)
  - Temperature and seed control
  - Direct Replicate API integration

#### `generateVoiceVits.py`
**Purpose**: VITS-based voice generation
- **Function**: `mindsflow_function(event, context)`
- **Input**: Text, voice model configuration
- **Output**: Synthesized speech with custom voice
- **Technology**: VITS (Variational Inference Text-to-Speech)
- **Key Features**:
  - Custom voice model inference
  - Voice cloning capabilities
  - API-based voice generation

---

### 🎞️ Video Assembly & Processing

#### `addSoundToVideo.py`
**Purpose**: Combine video with audio tracks
- **Function**: `mindsflow_function(event, context)`
- **Input**: Video URL, audio URL, volume settings
- **Output**: Video with synchronized audio
- **Technology**: MoviePy, NumPy
- **Key Features**:
  - Audio mixing and volume control
  - Audio repetition for longer videos
  - Composite audio track creation
  - Duration synchronization
  - AAC audio codec output

#### `addAudioSegmentsToVideo.py`
**Purpose**: Add segmented audio to video
- **Function**: `mindsflow_function(event, context)`
- **Input**: Video, multiple audio segments
- **Output**: Video with complex audio layering
- **Technology**: MoviePy, PyDub
- **Key Features**:
  - Multi-track audio composition
  - Segment timing control
  - Audio fade effects
  - Dynamic audio placement

---

### 📝 Caption & Subtitle Processing

#### `generateSrtFromJson.py`
**Purpose**: Generate SRT subtitle files from timing data
- **Function**: `mindsflow_function(event, context)`
- **Input**: JSON with sentence timing data
- **Output**: Formatted SRT subtitle file
- **Key Features**:
  - Azure time unit conversion
  - Sentence combining logic
  - Punctuation-aware splitting
  - Minimum word count enforcement
  - S3 upload integration

#### `AddCaptionsToVideoFFMPEG.py`
**Purpose**: Embed captions using FFmpeg
- **Function**: `mindsflow_function(event, context)`  
- **Input**: Video URL, SRT/ASS caption file
- **Output**: Video with burned-in captions
- **Technology**: FFmpeg, subprocess
- **Key Features**:
  - SRT and ASS subtitle support
  - Hardware-accelerated rendering
  - Caption positioning control
  - Batch caption processing

#### `AddCaptionsToVideoMoviepy.py`
**Purpose**: Embed captions using MoviePy
- **Function**: `mindsflow_function(event, context)`
- **Input**: Video, SRT file, styling parameters
- **Output**: Video with styled captions
- **Technology**: MoviePy, PyTTS
- **Key Features**:
  - Python-native caption rendering
  - Font and styling control
  - Position and timing management
  - Color and background effects

#### `AddCaptionsToVideoOpenCV.py`
**Purpose**: Embed captions using OpenCV
- **Function**: `mindsflow_function(event, context)`
- **Input**: Video, caption data, styling options
- **Output**: Video with pixel-perfect captions
- **Technology**: OpenCV, PIL
- **Key Features**:
  - Pixel-level caption control
  - Custom font rendering
  - Frame-by-frame processing
  - Advanced text effects

#### `ConvertSrtToAss.py`
**Purpose**: Convert SRT to ASS subtitle format
- **Function**: `mindsflow_function(event, context)`
- **Input**: SRT file URL
- **Output**: ASS format subtitle file
- **Technology**: PySubs2
- **Key Features**:
  - Format conversion between subtitle types
  - Styling preservation
  - S3 integration
  - Error handling for malformed subtitles

---

### 🌐 Translation & Localization

#### `translateSrtFile.py`
**Purpose**: Translate SRT subtitle files
- **Function**: `mindsflow_function(event, context)`
- **Input**: SRT file, source/target languages
- **Output**: Translated SRT file
- **Key Features**:
  - Preserve timing information
  - Multiple language support
  - Translation API integration
  - Subtitle format maintenance

#### `translateCaptionsJson.py`
**Purpose**: Translate JSON caption data
- **Function**: `mindsflow_function(event, context)`
- **Input**: Caption JSON, language parameters
- **Output**: Translated caption JSON
- **Key Features**:
  - JSON structure preservation
  - Timing data maintenance
  - Batch translation processing
  - Multi-language output

#### `translateTargetToSource.py`
**Purpose**: Bidirectional translation support
- **Function**: `mindsflow_function(event, context)`
- **Input**: Content, source/target language pair
- **Output**: Bidirectionally translated content
- **Key Features**:
  - Reverse translation capability
  - Quality verification
  - Language pair validation
  - Translation accuracy metrics

---

### 🎙️ Audio Processing & Analysis

#### `transcribeAudio.py`
**Purpose**: Convert speech to text with timestamps
- **Function**: `mindsflow_function(event, context)`
- **Input**: Audio file URL
- **Output**: Transcribed text with timing
- **Key Features**:
  - Speech-to-text conversion
  - Timestamp generation
  - Multi-language support
  - Accuracy optimization

#### `AudioTranscriptionToSentences.py`
**Purpose**: Split transcription into timed sentences
- **Function**: `mindsflow_function(event, context)`
- **Input**: Raw transcription, timing data
- **Output**: Sentence-segmented JSON
- **Technology**: NLTK, Jieba, Regex
- **Key Features**:
  - Intelligent sentence boundary detection
  - Multi-language sentence splitting (EN, ZH)
  - Timing preservation
  - Punctuation analysis
  - Azure time unit handling

#### `splitVoiceMusic.py`
**Purpose**: Separate voice from background music
- **Function**: `mindsflow_function(event, context)`
- **Input**: Mixed audio file
- **Output**: Separated voice and music tracks
- **Key Features**:
  - AI-powered source separation
  - Voice isolation
  - Music track extraction
  - Quality preservation

#### `generateAudioSegmentsFromJson.py`
**Purpose**: Create audio segments from JSON data
- **Function**: `mindsflow_function(event, context)`
- **Input**: JSON with audio timing data
- **Output**: Individual audio segment files
- **Key Features**:
  - Precise audio segmentation
  - Timing-based splitting
  - Multiple output formats
  - Batch processing

---

### 🔧 Utility & Support Functions

#### `loadJsonAndReturnKeys.py`
**Purpose**: JSON data extraction and key retrieval
- **Function**: `mindsflow_function(event, context)`
- **Input**: JSON URL or data
- **Output**: Extracted keys and values
- **Key Features**:
  - JSON parsing and validation
  - Key extraction utilities
  - Error handling
  - Data type conversion

#### `returnInputParameters.py`
**Purpose**: Parameter validation and processing
- **Function**: `mindsflow_function(event, context)`
- **Input**: Raw input parameters
- **Output**: Validated and processed parameters
- **Key Features**:
  - Input parameter validation
  - Default value assignment
  - Type checking and conversion
  - Error reporting

#### `setEpochInJsonFile.py`
**Purpose**: Training configuration management
- **Function**: `mindsflow_function(event, context)`
- **Input**: JSON config, epoch value
- **Output**: Updated configuration file
- **Key Features**:
  - Training parameter updates
  - JSON configuration management
  - S3 configuration storage
  - Version control

#### `ShowFonts.py`
**Purpose**: Font management for captions
- **Function**: `mindsflow_function(event, context)`
- **Input**: Font query parameters
- **Output**: Available fonts list
- **Key Features**:
  - System font enumeration
  - Font compatibility checking
  - Caption styling support
  - Cross-platform font handling

#### `addTextToImage.py`
**Purpose**: Add text overlays to images
- **Function**: `mindsflow_function(event, context)`
- **Input**: Image, text, positioning parameters
- **Output**: Image with text overlay
- **Technology**: OpenCV, PIL
- **Key Features**:
  - Text positioning control
  - Font and styling options
  - Image composition
  - Batch text processing

---

### 🗑️ Cleanup & Maintenance

#### `deleteFilesByExtension.py`
**Purpose**: Clean up temporary files by extension
- **Function**: `mindsflow_function(event, context)`
- **Input**: Directory path, file extensions
- **Output**: Cleanup status report
- **Key Features**:
  - Selective file deletion
  - Extension-based filtering
  - Safety checks
  - Batch cleanup operations

#### `deleteFolders.py`
**Purpose**: Remove temporary directories
- **Function**: `mindsflow_function(event, context)`
- **Input**: Folder paths to delete
- **Output**: Deletion status
- **Key Features**:
  - Recursive directory removal
  - Safety validation
  - Error handling
  - Cleanup reporting

---

### 📤 Upload & Distribution

#### `UploadResultZipS3.py`
**Purpose**: Package and upload final results
- **Function**: `mindsflow_function(event, context)`
- **Input**: Video, thumbnails, scripts, captions
- **Output**: ZIP file download URL
- **Key Features**:
  - Multi-file ZIP packaging
  - S3 upload optimization
  - Download link generation
  - Package integrity verification

#### `uploadYoutubeVideo.py`
**Purpose**: Upload videos to YouTube
- **Function**: `mindsflow_function(event, context)`
- **Input**: Video URL, metadata, credentials
- **Output**: Upload success status
- **Technology**: YouTube Upload API
- **Key Features**:
  - YouTube API authentication
  - Video metadata management
  - Category and privacy settings
  - Upload progress tracking
  - Multi-account support

---

### 🔗 Platform Integration

#### `MindsflowAgent.py`
**Purpose**: Mindsflow platform integration
- **Function**: `mindsflow_function(event, context)`
- **Input**: Agent parameters and context
- **Output**: Mindsflow API responses
- **Key Features**:
  - Platform API integration
  - Agent orchestration
  - Response handling
  - Error management

#### `CommandsExecution.py`
**Purpose**: System command execution
- **Function**: `mindsflow_function(event, context)`
- **Input**: Command strings and parameters
- **Output**: Command execution results
- **Key Features**:
  - Safe command execution
  - Output capture
  - Error handling
  - Security validation

---

## 🎤 Voice Clone System
*Location: `voice_clone/`*

### Core Voice Cloning

#### `voice_clone_api/train_api.py`
**Purpose**: FastAPI server for voice model training
- **Framework**: FastAPI + Uvicorn
- **Endpoints**: Training management, file upload
- **Key Features**:
  - RESTful training API
  - File upload handling
  - Training progress monitoring
  - Model management

#### `voice_clone_api/infer_api.py`  
**Purpose**: FastAPI server for voice inference
- **Framework**: FastAPI + Uvicorn
- **Endpoints**: Voice generation, model loading
- **Key Features**:
  - Real-time voice synthesis
  - Model switching
  - Audio file responses
  - API rate limiting

#### `voice_clone_api/train.py`
**Purpose**: Voice model training engine
- **Technology**: VITS, PyTorch
- **Input**: Training audio samples
- **Output**: Trained voice models
- **Key Features**:
  - VITS model training
  - Audio preprocessing
  - Training progress tracking
  - Model checkpointing

#### `voice_clone_api/infer.py`
**Purpose**: Voice synthesis inference engine
- **Technology**: VITS model inference
- **Input**: Text + voice model
- **Output**: Synthesized speech
- **Key Features**:
  - Fast inference
  - Quality voice synthesis
  - Batch processing
  - GPU acceleration

#### `voice_clone_api/functions.py`
**Purpose**: Core voice processing utilities
- **Functions**: Audio processing, noise reduction
- **Technology**: PyDub, NoiseReduce, SciPy
- **Key Features**:
  - Audio preprocessing
  - Noise reduction
  - File format conversion
  - Quality enhancement

### Voice Clone Integration Functions

#### `functions/clone_voice_vits.py`
**Purpose**: Mindsflow integration for VITS voice cloning
- **Function**: `mindsflow_function(event, context)`
- **Input**: Audio sample, training parameters
- **Output**: Trained voice model URL
- **Key Features**:
  - API integration wrapper
  - S3 model storage
  - Training job management
  - Status monitoring

#### `functions/generate_voice_vits.py`
**Purpose**: Mindsflow integration for VITS voice generation
- **Function**: `mindsflow_function(event, context)`
- **Input**: Text, voice model ID
- **Output**: Generated speech URL
- **Key Features**:
  - Voice synthesis API wrapper
  - Model loading
  - Audio generation
  - S3 upload integration

#### `functions/set_epoch_in_json_config.py`
**Purpose**: Training configuration management
- **Function**: `mindsflow_function(event, context)`
- **Input**: Config JSON, epoch settings
- **Output**: Updated configuration
- **Key Features**:
  - Training parameter updates
  - JSON configuration handling
  - S3 config storage
  - Version management

---

## 📊 File Dependency Matrix

| Function | Dependencies | Outputs To | Technology Stack |
|----------|-------------|------------|-----------------|
| `generateVideoScript.py` | GPT-4, Mindsflow | `PromptImagesToVideo.py`, `textToSpeech.py`, `MusicGeneration.py` | OpenAI, AWS S3 |
| `PromptImagesToVideo.py` | Script JSON | `addSoundToVideo.py` | DALL-E 3, SDXL, MoviePy |
| `textToSpeech.py` | Script text | `addSoundToVideo.py` | Azure TTS, PyDub |
| `MusicGeneration.py` | Music prompt | `addSoundToVideo.py` | Meta MusicGen, Replicate |
| `addSoundToVideo.py` | Video + Audio | `AddCaptionsToVideoFFMPEG.py` | MoviePy, NumPy |
| `generateSrtFromJson.py` | Timing JSON | Caption integration | Python, Regex |
| `AddCaptionsToVideoFFMPEG.py` | Video + SRT | `UploadResultZipS3.py` | FFmpeg, Subprocess |
| `UploadResultZipS3.py` | Final assets | Distribution | AWS S3, ZIP |

---

## 🔄 Processing Flow Summary

1. **Input Processing**: `returnInputParameters.py` validates input
2. **Content Generation**: `generateVideoScript.py` creates script
3. **Asset Creation**: Parallel generation of audio, video, music
4. **Integration**: `addSoundToVideo.py` combines media
5. **Caption Processing**: SRT generation and video integration  
6. **Packaging**: `UploadResultZipS3.py` creates final deliverable
7. **Distribution**: Optional YouTube upload or S3 delivery

This comprehensive file reference provides complete visibility into every component of the AI Video Generator system, enabling efficient development, maintenance, and troubleshooting.