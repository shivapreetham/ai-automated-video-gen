'use client';

import { useState, useCallback, useEffect } from 'react';

export default function ClientSideYouTubeUploader({ videoUrl, videoTitle, onUploadSuccess, onUploadError }) {
  const [user, setUser] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [accessToken, setAccessToken] = useState(null);

  // Initialize Google Identity Services
  useEffect(() => {
    const initializeGoogleIdentityServices = async () => {
      // Wait for Google Identity Services to load
      let attempts = 0;
      while (!window.google?.accounts?.oauth2 && attempts < 50) {
        await new Promise(resolve => setTimeout(resolve, 200));
        attempts++;
      }

      if (!window.google?.accounts?.oauth2) {
        onUploadError?.('Google Identity Services failed to load. Please refresh the page.');
        return;
      }

      try {
        console.log('Initializing Google Identity Services...');
        console.log('Client ID:', process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID);

        // Initialize the token client for YouTube upload
        window.tokenClient = google.accounts.oauth2.initTokenClient({
          client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
          scope: 'https://www.googleapis.com/auth/youtube.upload',
          callback: (tokenResponse) => {
            console.log('Token response received:', tokenResponse);
            if (tokenResponse.error) {
              console.error('Token error:', tokenResponse.error);
              onUploadError?.('Authentication failed: ' + tokenResponse.error);
              setIsAuthenticating(false);
              return;
            }
            
            if (tokenResponse.access_token) {
              console.log('Access token obtained successfully');
              setAccessToken(tokenResponse.access_token);
              
              // Get user info using the access token
              getUserInfo(tokenResponse.access_token);
            }
            setIsAuthenticating(false);
          },
        });

        setIsInitialized(true);
        console.log('Google Identity Services initialized successfully');

      } catch (error) {
        console.error('Google Identity Services initialization error:', error);
        onUploadError?.('Failed to initialize Google Identity Services: ' + error.message);
      }
    };

    initializeGoogleIdentityServices();
  }, [onUploadError]);

  // Get user information using access token
  const getUserInfo = async (token) => {
    try {
      const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const userInfo = await response.json();
        console.log('User info retrieved:', userInfo.name);
        setUser({
          name: userInfo.name,
          email: userInfo.email,
          picture: userInfo.picture,
        });
      }
    } catch (error) {
      console.error('Failed to get user info:', error);
    }
  };

  const handleSignIn = useCallback(async () => {
    if (!isInitialized || !window.tokenClient) {
      onUploadError?.('Google Identity Services not yet initialized. Please wait a moment and try again.');
      return;
    }

    setIsAuthenticating(true);
    
    try {
      console.log('Starting OAuth flow...');
      
      // Request access token
      window.tokenClient.requestAccessToken();
      
    } catch (error) {
      console.error('Sign-in failed:', error);
      onUploadError?.('Sign-in failed: ' + error.message);
      setIsAuthenticating(false);
    }
  }, [isInitialized, onUploadError]);

  const handleSignOut = useCallback(() => {
    if (accessToken) {
      // Revoke the token
      google.accounts.oauth2.revoke(accessToken);
    }
    setUser(null);
    setAccessToken(null);
  }, [accessToken]);

  const downloadVideoFromCloudflare = useCallback(async (url) => {
    try {
      console.log('Downloading video from Cloudflare:', url);
      
      // Add CORS proxy if needed or handle CORS properly
      const response = await fetch(url, {
        mode: 'cors',
        credentials: 'omit'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to download: ${response.status} ${response.statusText}`);
      }
      
      const blob = await response.blob();
      console.log('Video downloaded successfully, size:', (blob.size / (1024 * 1024)).toFixed(2), 'MB');
      return blob;
    } catch (error) {
      console.error('Download failed:', error);
      throw new Error('Failed to download video from Cloudflare: ' + error.message);
    }
  }, []);

  const uploadToYouTube = useCallback(async (videoBlob, title, description, tags) => {
    if (!accessToken) {
      throw new Error('User not authenticated - no access token');
    }

    setUploadProgress(5);

    try {
      console.log('Starting YouTube upload...');
      
      // Prepare metadata
      const metadata = {
        snippet: {
          title: title,
          description: description,
          tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0),
          categoryId: '22', // People & Blogs
          defaultLanguage: 'en'
        },
        status: {
          privacyStatus: 'public',
          selfDeclaredMadeForKids: false
        }
      };

      setUploadProgress(10);

      // Step 1: Initialize resumable upload
      console.log('Initializing resumable upload...');
      const initResponse = await fetch('https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
          'X-Upload-Content-Type': 'video/mp4',
          'X-Upload-Content-Length': videoBlob.size.toString()
        },
        body: JSON.stringify(metadata)
      });

      if (!initResponse.ok) {
        const errorText = await initResponse.text();
        console.error('Upload init failed:', initResponse.status, errorText);
        throw new Error(`Upload initialization failed: ${initResponse.status} - ${errorText}`);
      }

      const uploadUrl = initResponse.headers.get('Location');
      if (!uploadUrl) {
        throw new Error('No upload URL received from YouTube');
      }

      console.log('Upload URL obtained, starting chunked upload...');
      setUploadProgress(15);

      // Step 2: Upload video in chunks
      const chunkSize = 1024 * 1024 * 8; // 8MB chunks
      let start = 0;
      const totalSize = videoBlob.size;

      while (start < totalSize) {
        const end = Math.min(start + chunkSize, totalSize);
        const chunk = videoBlob.slice(start, end);
        
        console.log(`Uploading chunk: ${start}-${end-1}/${totalSize}`);
        
        const chunkResponse = await fetch(uploadUrl, {
          method: 'PUT',
          headers: {
            'Content-Range': `bytes ${start}-${end - 1}/${totalSize}`
          },
          body: chunk
        });

        const progress = Math.round(15 + ((start / totalSize) * 80)); // 15% to 95%
        setUploadProgress(progress);

        if (chunkResponse.status === 308) {
          // Continue uploading
          start = end;
        } else if (chunkResponse.status === 200 || chunkResponse.status === 201) {
          // Upload complete
          const result = await chunkResponse.json();
          console.log('Upload completed successfully:', result.id);
          setUploadProgress(100);
          return result;
        } else {
          const errorText = await chunkResponse.text();
          console.error('Chunk upload failed:', chunkResponse.status, errorText);
          throw new Error(`Upload failed: ${chunkResponse.status} - ${errorText}`);
        }
      }

    } catch (error) {
      console.error('YouTube upload error:', error);
      throw error;
    }
  }, [accessToken]);

  const handleUpload = useCallback(async () => {
    if (!videoUrl || !accessToken) {
      onUploadError?.('Missing video URL or authentication');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    
    try {
      // Step 1: Download video from Cloudflare
      console.log('Step 1: Downloading video from Cloudflare...');
      const videoBlob = await downloadVideoFromCloudflare(videoUrl);
      
      // Step 2: Upload to YouTube
      console.log('Step 2: Uploading to YouTube...');
      const result = await uploadToYouTube(
        videoBlob,
        videoTitle || 'AI Generated Video #Shorts',
        `Generated with AI Video Generator

This video was created using artificial intelligence.

#Shorts #AI #Generated #ArtificialIntelligence #VideoGenerator`,
        'AI,Generated,Shorts,Video,ArtificialIntelligence,VideoGenerator'
      );

      const videoId = result.id;
      const uploadResult = {
        videoId: videoId,
        youtubeUrl: `https://www.youtube.com/watch?v=${videoId}`,
        shortsUrl: `https://www.youtube.com/shorts/${videoId}`,
        title: result.snippet?.title || videoTitle,
        status: result.status?.uploadStatus
      };

      console.log('Upload successful:', uploadResult);
      onUploadSuccess?.(uploadResult);

    } catch (error) {
      console.error('Complete upload process failed:', error);
      onUploadError?.('Upload failed: ' + error.message);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [videoUrl, videoTitle, accessToken, downloadVideoFromCloudflare, uploadToYouTube, onUploadSuccess, onUploadError]);

  if (!isInitialized) {
    return (
      <div className="p-4 bg-blue-900/20 border border-blue-500/20 rounded-lg">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-blue-300">Initializing Google Identity Services...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {!user ? (
        <div className="p-4 bg-blue-900/20 border border-blue-500/20 rounded-lg">
          <h4 className="text-white font-medium mb-2">Sign in to YouTube</h4>
          <p className="text-gray-400 text-sm mb-3">
            Sign in with your Google account to upload videos to YouTube. This will request permission to upload videos to your channel.
          </p>
          <button
            onClick={handleSignIn}
            disabled={isAuthenticating}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {isAuthenticating ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
            )}
            <span>{isAuthenticating ? 'Signing in...' : 'Sign in with Google'}</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="p-4 bg-green-900/20 border border-green-500/20 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <img
                  src={user.picture}
                  alt={user.name}
                  className="w-8 h-8 rounded-full"
                />
                <div>
                  <p className="text-white font-medium">{user.name}</p>
                  <p className="text-gray-400 text-sm">{user.email}</p>
                  <p className="text-green-400 text-xs">✓ Authenticated for YouTube upload</p>
                </div>
              </div>
              <button
                onClick={handleSignOut}
                className="px-3 py-1 text-gray-400 hover:text-white text-sm transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>

          {isUploading && (
            <div className="p-4 bg-yellow-900/20 border border-yellow-500/20 rounded-lg">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-5 h-5 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-yellow-300 font-medium">
                  {uploadProgress < 15 ? 'Downloading from Cloudflare...' : 
                   uploadProgress < 95 ? `Uploading to YouTube... ${uploadProgress}%` : 
                   'Finalizing upload...'}
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-yellow-400 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="text-gray-400 text-xs mt-2">
                This may take a few minutes depending on video size
              </p>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={isUploading || !videoUrl}
            className="w-full px-6 py-3 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
            </svg>
            <span>{isUploading ? 'Uploading...' : 'Upload to YouTube'}</span>
          </button>

          {!videoUrl && (
            <p className="text-gray-400 text-sm text-center">
              Generate a video first to enable YouTube upload
            </p>
          )}
        </div>
      )}
    </div>
  );
}