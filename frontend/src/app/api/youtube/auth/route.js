import { google } from 'googleapis';
import { NextResponse } from 'next/server';

const oauth2Client = new google.auth.OAuth2(
  process.env.GOOGLE_CLIENT_ID,
  process.env.GOOGLE_CLIENT_SECRET,
  `${process.env.NEXTAUTH_URL}/api/youtube/callback`
);

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get('action');

    if (action === 'login') {
      // Generate OAuth URL for YouTube access
      const authUrl = oauth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: [
          'https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/youtube',
          'https://www.googleapis.com/auth/userinfo.profile'
        ],
        state: 'youtube_upload' // To identify this flow
      });

      return NextResponse.json({ authUrl });
    }

    return NextResponse.json({ error: 'Invalid action' }, { status: 400 });

  } catch (error) {
    console.error('YouTube auth error:', error);
    return NextResponse.json(
      { error: 'Authentication failed', details: error.message },
      { status: 500 }
    );
  }
}