# YouTube Auto-Upload Setup Instructions

## 🔧 Server-Side YouTube Upload Configuration

This system now uses **server-side automatic uploads** instead of browser-based uploads. Videos are uploaded directly from the backend to YouTube and the user receives the YouTube URL.

## Setup Steps

### 1. Google Cloud Console Configuration

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Enable YouTube Data API v3**
   - Go to APIs & Services > Library
   - Search for "YouTube Data API v3"
   - Click "Enable"

3. **Configure OAuth Consent Screen**
   - Go to APIs & Services > OAuth consent screen
   - Choose "External" user type
   - Fill in required fields:
     - App name: "AI Video Generator"
     - User support email: your email
     - Developer contact: your email
   - Add scopes: `https://www.googleapis.com/auth/youtube.upload`
   - Save and continue

4. **Create OAuth 2.0 Client ID**
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Application type: **"Desktop application"** (IMPORTANT: NOT Web application)
   - Name: "AI Video Generator Backend"
   - Click "Create"
   - Copy the Client ID and Client Secret (you don't need to download JSON for desktop apps)

### 2. Get Refresh Token

1. **Add Credentials to .env**
   ```
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   ```

2. **Run Token Generator**
   ```bash
   python get_youtube_token.py
   ```
   - This will open a browser window
   - Authorize the application
   - Copy the generated refresh token

3. **Add Refresh Token to .env**
   ```
   YOUTUBE_REFRESH_TOKEN=your_refresh_token_here
   ```

### 3. Final .env Configuration

Your `.env` file should contain:
```
# YouTube Auto-Upload Configuration
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
YOUTUBE_REFRESH_TOKEN=your_refresh_token_here
```

## 🎬 How It Works

1. **Video Generation**: User generates video normally
2. **Auto Upload**: Click "Upload to YouTube" button
3. **Server Upload**: Backend uploads directly to YouTube
4. **Get URL**: User receives YouTube URL immediately

## ✅ Features

- ✅ **Automatic upload** - No manual steps
- ✅ **Server-side** - No browser authentication needed
- ✅ **Direct URLs** - Get YouTube URL instantly
- ✅ **Customizable** - Title, description, tags
- ✅ **YouTube Shorts** - Optimized for Shorts format

## 🔍 Testing

1. **Check Configuration**:
   ```bash
   curl http://localhost:8000/youtube/status
   ```

2. **Test Upload**:
   - Generate a video
   - Click "Upload to YouTube" 
   - Fill in details and upload

## 🚨 Troubleshooting

### YouTube API Errors
- **403 Quota Exceeded**: Wait 24 hours or increase quota
- **401 Unauthorized**: Refresh token expired, regenerate
- **404 Channel Not Found**: Make sure your account has a YouTube channel

### Configuration Issues
- **Not Configured**: Missing credentials in .env
- **Invalid Credentials**: Check client ID/secret
- **Expired Token**: Run `get_youtube_token.py` again

## 📊 Status Endpoint

Check YouTube configuration status:
- **GET** `http://localhost:8000/youtube/status`

Returns:
```json
{
  "configured": true,
  "ready_for_upload": true,
  "quota_check": {
    "success": true,
    "message": "YouTube API access is working"
  }
}
```