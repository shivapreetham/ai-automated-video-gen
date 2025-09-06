# Local AI Video Generator Setup Guide

## 🎯 Free Local Setup Overview

This guide shows how to run the AI Video Generator on your laptop using **100% free alternatives** to the paid APIs:

### 🔄 Service Replacements
| Original (Paid) | Local Alternative (Free) | Notes |
|-----------------|-------------------------|-------|
| Azure Text-to-Speech | Google TTS (gTTS) | Multiple languages, good quality |
| OpenAI DALL-E 3 | Pollinations AI | Free, multiple models, good quality |
| Stable Diffusion XL | Pollinations AI | Same API, different models |
| Meta MusicGen | *(Skip for now)* | Can be added later |
| AWS S3 Storage | Local File System | Files stored locally |
| Mindsflow GPT-4 | Simple Script Templates | Basic but functional |

---

## 🛠️ System Requirements

### Minimum Hardware
- **RAM**: 8GB (16GB recommended)
- **Storage**: 5GB free space
- **Internet**: Required for image generation (Pollinations AI)
- **OS**: Windows 10+, macOS 10.14+, or Linux

### Required Software
1. **Python 3.8-3.11** (Python 3.12 may have compatibility issues)
2. **FFmpeg** (for video processing)
3. **Git** (for cloning repository)

---

## 📦 Installation Steps

### Step 1: Install System Dependencies

#### Windows:
```bash
# Install FFmpeg
# Download from https://ffmpeg.org/download.html
# Extract and add to PATH, or use chocolatey:
choco install ffmpeg

# Verify installation
ffmpeg -version
```

#### macOS:
```bash
# Install FFmpeg using Homebrew
brew install ffmpeg

# Verify installation
ffmpeg -version
```

#### Linux (Ubuntu/Debian):
```bash
# Install FFmpeg
sudo apt update
sudo apt install ffmpeg

# Verify installation
ffmpeg -version
```

### Step 2: Set Up Python Environment

```bash
# Navigate to project directory
cd ai-video-generator

# Create virtual environment
python -m venv venv_local

# Activate virtual environment
# Windows:
venv_local\Scripts\activate
# macOS/Linux:
source venv_local/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements_local.txt
```

### Step 3: Test Installation

```bash
# Navigate to local functions
cd local_functions

# Test text-to-speech
python -c "from textToSpeech_gtts import generate_speech_local; generate_speech_local('Hello world')"

# Test image generation
python -c "from PromptImagesToVideo_pollinations import generate_image_pollinations; print(generate_image_pollinations('test image'))"
```

---

## 🚀 Usage

### Simple Command Line Usage

```bash
cd local_functions
python local_video_generator.py "Benefits of eating apples"
```

### Advanced Usage with Parameters

```bash
python local_video_generator.py "Space exploration" \
    --width 1080 \
    --height 1920 \
    --fps 24 \
    --duration 15 \
    --output my_videos
```

### Python Script Usage

```python
from local_functions.local_video_generator import LocalVideoGenerator

# Create generator
generator = LocalVideoGenerator(output_dir="my_videos")

# Generate video
result = generator.generate_video(
    topic="Benefits of meditation",
    width=1080,
    height=1920,
    fps=24,
    voice_speed=1.2
)

if result['success']:
    print(f"Video created: {result['final_video']}")
else:
    print(f"Error: {result['error']}")
```

---

## 📁 Local Architecture

### File Structure
```
ai-video-generator/
├── local_functions/              # Free alternatives
│   ├── textToSpeech_gtts.py     # gTTS implementation
│   ├── PromptImagesToVideo_pollinations.py  # Pollinations AI
│   ├── local_video_generator.py  # Main orchestrator
│   └── output/                   # Generated videos
├── docs/                         # Documentation
├── requirements_local.txt        # Free dependencies
└── venv_local/                   # Virtual environment
```

### Processing Flow (Local)
```
Topic Input → Simple Script → gTTS Speech → Pollinations Images → MoviePy Assembly → Local Video
```

---

## 🎮 Available Features

### ✅ Working Features
- **Text-to-Speech**: Multiple languages via gTTS
- **Image Generation**: High-quality images via Pollinations AI
- **Video Assembly**: Transitions, zoom effects, timing
- **Local Storage**: All files stored locally
- **Batch Processing**: Multiple videos in one session

### 🔧 Configurable Options
```python
params = {
    "topic": "Your video topic",
    "language": "en",  # en, es, fr, de, it, zh, etc.
    "voice_speed": 1.0,  # 0.5-2.0
    "width": 1080,       # Video width
    "height": 1920,      # Video height (9:16 for mobile)
    "fps": 24,           # Frames per second
    "image_duration": 6, # Seconds per image
    "transition_time": 1, # Crossfade duration
    "zoom": 1.1,         # Zoom effect strength
    "img_model": "flux"  # Pollinations model
}
```

### 🎨 Pollinations AI Models
- **flux** (default): High quality, balanced
- **turbo**: Faster generation
- **flux-realism**: Photorealistic images
- **flux-anime**: Anime/cartoon style

---

## 🔧 Troubleshooting

### Common Issues

#### 1. FFmpeg Not Found
```
Error: ffmpeg not found in PATH
```
**Solution**: Install FFmpeg and add to system PATH

#### 2. gTTS Network Error
```
Error: gTTS request failed
```
**Solution**: Check internet connection, try different language

#### 3. Image Generation Timeout
```
Error: Pollinations API timeout
```
**Solution**: Retry, check internet, use simpler prompts

#### 4. MoviePy Installation Issues
```
Error: Failed building wheel for moviepy
```
**Solution**: 
```bash
pip install --upgrade setuptools wheel
pip install moviepy --no-cache-dir
```

### Performance Tips

1. **Reduce Video Resolution**: Use 720p instead of 1080p for faster processing
2. **Lower FPS**: Use 16fps instead of 24fps
3. **Shorter Durations**: Start with 10-15 second videos
4. **Simple Prompts**: Use clear, simple image prompts

---

## 🔄 Upgrading to Paid Services Later

If you want to upgrade to paid services later:

1. **Add OpenAI API**: Replace simple script generation with GPT-4
2. **Add Azure TTS**: Better voice quality and more speakers
3. **Add AWS S3**: Cloud storage and sharing
4. **Add MusicGen**: Background music generation

The architecture is designed to easily swap components.

---

## 📊 Expected Performance

### Processing Times (on average laptop)
- **Script Generation**: < 1 second
- **Speech Generation**: 5-15 seconds
- **Image Generation**: 10-30 seconds per image
- **Video Assembly**: 30-60 seconds
- **Total**: 2-5 minutes for 15-second video

### Quality Expectations
- **Speech**: Good quality, natural-sounding
- **Images**: High quality, artistic style
- **Video**: Professional transitions and effects
- **Overall**: Suitable for social media, presentations

---

## 🎯 Next Steps

1. **Test the basic setup** with a simple topic
2. **Experiment with parameters** to find your preferred style
3. **Create multiple videos** to build familiarity
4. **Consider paid upgrades** for production use
5. **Customize prompts** for your specific needs

This local setup gives you a fully functional AI video generator without any monthly subscriptions or API costs!