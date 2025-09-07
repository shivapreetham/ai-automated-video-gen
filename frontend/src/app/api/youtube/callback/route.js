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
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    if (error) {
      // User denied access
      return NextResponse.redirect(`${process.env.NEXTAUTH_URL}?youtube_error=${error}`);
    }

    if (!code) {
      return NextResponse.json({ error: 'No authorization code received' }, { status: 400 });
    }

    // Exchange code for tokens
    const { tokens } = await oauth2Client.getToken(code);
    
    // Get user info
    oauth2Client.setCredentials(tokens);
    const oauth2 = google.oauth2({ version: 'v2', auth: oauth2Client });
    const userInfo = await oauth2.userinfo.get();

    // Store tokens in session/cookie (simplified approach)
    const response = NextResponse.redirect(`${process.env.NEXTAUTH_URL}?youtube_auth=success`);
    
    // Store tokens in HTTP-only cookies (more secure than localStorage)
    response.cookies.set('youtube_access_token', tokens.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 3600 // 1 hour
    });
    
    if (tokens.refresh_token) {
      response.cookies.set('youtube_refresh_token', tokens.refresh_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        maxAge: 30 * 24 * 60 * 60 // 30 days
      });
    }

    // Store user info
    response.cookies.set('youtube_user', JSON.stringify({
      name: userInfo.data.name,
      email: userInfo.data.email,
      picture: userInfo.data.picture
    }), {
      httpOnly: false, // Allow frontend access
      secure: process.env.NODE_ENV === 'production',
      maxAge: 3600
    });

    return response;

  } catch (error) {
    console.error('YouTube callback error:', error);
    return NextResponse.redirect(`${process.env.NEXTAUTH_URL}?youtube_error=callback_failed`);
  }
}