# Akash Story Generation Service Deployment

## Overview
Simple Gemini-powered story generation service deployable on Akash Network.

## Features
- **Story Generation**: `/generate-story` - Create stories with customizable genre, length, and style
- **Script Generation**: `/generate-script` - Generate video scripts (existing functionality) 
- **Health Check**: `/health` - Service status and API configuration check
- **No Auth Required**: Completely open access
- **Fallback Mode**: Works even without Gemini API key (provides template stories)

## Quick Deploy

1. **Set your Gemini API Key** (optional but recommended):
   ```bash
   export GEMINI_API_KEY="your_actual_api_key_here"
   ```

2. **Deploy to Akash**:
   ```bash
   akash tx deployment create akash-script-deploy.yaml --from your-wallet --gas-prices 0.025uakt --gas auto
   ```

## API Usage

### Generate Story
```bash
curl -X POST http://your-deployment-url/generate-story \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "space adventure",
    "genre": "sci-fi", 
    "length": "short",
    "style": "exciting"
  }'
```

**Parameters:**
- `topic` (required): Story topic
- `genre` (optional): sci-fi, fantasy, mystery, romance, general (default: general)
- `length` (optional): short, medium, long (default: short)
- `style` (optional): exciting, dramatic, humorous, engaging (default: engaging)

### Health Check
```bash
curl http://your-deployment-url/health
```

## Configuration

The deployment will work immediately with fallback stories. To use Gemini AI:

1. Get a Gemini API key from Google AI Studio
2. Set the `GEMINI_API_KEY` environment variable before deployment
3. Or update the YAML file directly with your key

## Service Resources
- **CPU**: 1 core
- **Memory**: 2GB RAM  
- **Storage**: 2GB
- **Cost**: ~100 uAKT per deployment

## Access
Once deployed, your service will be publicly accessible at the Akash provider URL with no authentication required.