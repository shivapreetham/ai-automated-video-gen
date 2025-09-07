import { google } from 'googleapis';
import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function POST(request) {
  try {
    const cookieStore = await cookies();
    const accessToken = cookieStore.get('youtube_access_token')?.value;
    const refreshToken = cookieStore.get('youtube_refresh_token')?.value;

    if (!accessToken) {
      return NextResponse.json({ error: 'Not authenticated with YouTube' }, { status: 401 });
    }

    // Get upload data
    const formData = await request.formData();
    const videoFile = formData.get('video');
    const title = formData.get('title') || 'AI Generated Video #Shorts';
    const description = formData.get('description') || 'Generated with AI Video Generator';
    const tags = formData.get('tags') || 'AI,Shorts,Generated,Video';
    const jobId = formData.get('jobId');

    if (!videoFile) {
      // If no video file, expect a Flask job ID to download from
      if (!jobId) {
        return NextResponse.json({ error: 'No video file or job ID provided' }, { status: 400 });
      }

      // Download video from Flask backend
      const flaskResponse = await fetch(`http://localhost:8000/jobs/${jobId}/download`);
      if (!flaskResponse.ok) {
        return NextResponse.json({ error: 'Failed to download video from backend' }, { status: 400 });
      }
      
      const videoBuffer = await flaskResponse.arrayBuffer();
      const videoBlob = new Blob([videoBuffer], { type: 'video/mp4' });
      
      return await uploadToYouTube(videoBlob, title, description, tags, accessToken, refreshToken);
    }

    // Direct file upload
    const videoBuffer = await videoFile.arrayBuffer();
    const videoBlob = new Blob([videoBuffer], { type: 'video/mp4' });
    
    return await uploadToYouTube(videoBlob, title, description, tags, accessToken, refreshToken);

  } catch (error) {
    console.error('YouTube upload error:', error);
    return NextResponse.json(
      { error: 'Upload failed', details: error.message },
      { status: 500 }
    );
  }
}

async function uploadToYouTube(videoBlob, title, description, tags, accessToken, refreshToken) {
  try {
    // Set up OAuth2 client
    const oauth2Client = new google.auth.OAuth2(
      process.env.GOOGLE_CLIENT_ID,
      process.env.GOOGLE_CLIENT_SECRET,
      `${process.env.NEXTAUTH_URL}/api/youtube/callback`
    );

    oauth2Client.setCredentials({
      access_token: accessToken,
      refresh_token: refreshToken
    });

    const youtube = google.youtube({ version: 'v3', auth: oauth2Client });

    // Prepare video metadata for YouTube Shorts
    const videoMetadata = {
      snippet: {
        title: title + (title.includes('#Shorts') ? '' : ' #Shorts'),
        description: description + '\n\n#Shorts #AI #Generated',
        tags: tags.split(',').map(tag => tag.trim()),
        categoryId: '22', // People & Blogs category
        defaultLanguage: 'en',
        defaultAudioLanguage: 'en'
      },
      status: {
        privacyStatus: 'public', // or 'unlisted' for private sharing
        selfDeclaredMadeForKids: false
      }
    };

    // Convert blob to readable stream
    const videoBuffer = Buffer.from(await videoBlob.arrayBuffer());
    const { Readable } = require('stream');
    const videoStream = Readable.from(videoBuffer);

    // Upload video to YouTube
    console.log('Starting YouTube upload...');
    const uploadResponse = await youtube.videos.insert({
      part: ['snippet', 'status'],
      resource: videoMetadata,
      media: {
        body: videoStream
      }
    });

    const videoId = uploadResponse.data.id;
    const youtubeUrl = `https://www.youtube.com/watch?v=${videoId}`;
    const shortsUrl = `https://www.youtube.com/shorts/${videoId}`;

    console.log('YouTube upload successful:', youtubeUrl);

    return NextResponse.json({
      success: true,
      videoId: videoId,
      youtubeUrl: youtubeUrl,
      shortsUrl: shortsUrl,
      title: uploadResponse.data.snippet.title,
      message: 'Video uploaded to YouTube successfully!'
    });

  } catch (error) {
    console.error('YouTube API error:', error);
    
    // Handle specific YouTube API errors
    if (error.code === 403) {
      return NextResponse.json({ 
        error: 'YouTube API quota exceeded or channel not verified for uploads',
        details: error.message 
      }, { status: 403 });
    }
    
    if (error.code === 401) {
      return NextResponse.json({ 
        error: 'YouTube authentication expired',
        details: 'Please re-authenticate with YouTube' 
      }, { status: 401 });
    }

    return NextResponse.json({ 
      error: 'YouTube upload failed',
      details: error.message 
    }, { status: 500 });
  }
}