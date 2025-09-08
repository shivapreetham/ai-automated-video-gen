"""
YouTube Upload Backend Module
Handles automatic video uploads to YouTube using stored refresh tokens
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class YouTubeUploader:
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.refresh_token = os.getenv('YOUTUBE_REFRESH_TOKEN')
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            print("Warning: YouTube credentials not fully configured")
            self.configured = False
        else:
            self.configured = True
    
    def get_access_token(self) -> Optional[str]:
        """Get fresh access token using refresh token"""
        
        if not self.configured:
            return None
        
        try:
            # Google OAuth2 token refresh endpoint
            token_url = "https://oauth2.googleapis.com/token"
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data.get('access_token')
            
        except Exception as e:
            print(f"[ERROR] Failed to refresh access token: {e}")
            return None
    
    def upload_video(self, video_file_path: str, title: str, description: str = "", tags: list = None) -> Dict[str, Any]:
        """
        Upload video to YouTube and return URL using Google API Client
        """
        
        if not self.configured:
            return {
                "success": False,
                "error": "YouTube uploader not configured. Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN in .env"
            }
        
        if not os.path.exists(video_file_path):
            return {
                "success": False,
                "error": f"Video file not found: {video_file_path}"
            }
        
        # Check if using placeholder token for testing
        if "PLACEHOLDER" in self.refresh_token:
            print("[YOUTUBE] TEST MODE: Using placeholder token")
            print(f"[YOUTUBE] Would upload: {video_file_path}")
            print(f"[YOUTUBE] Title: {title}")
            print(f"[YOUTUBE] Description: {description[:100]}...")
            
            # Generate test YouTube URL
            import random
            test_video_id = f"TEST_{random.randint(100000, 999999)}"
            test_youtube_url = f"https://www.youtube.com/watch?v={test_video_id}"
            test_shorts_url = f"https://www.youtube.com/shorts/{test_video_id}"
            
            print(f"[YOUTUBE] TEST SUCCESS! Would return:")
            print(f"[YOUTUBE] YouTube URL: {test_youtube_url}")
            print(f"[YOUTUBE] Shorts URL: {test_shorts_url}")
            
            return {
                "success": True,
                "video_id": test_video_id,
                "youtube_url": test_youtube_url,
                "shorts_url": test_shorts_url,
                "title": title,
                "upload_time": datetime.now().isoformat(),
                "privacy_status": "public",
                "test_mode": True,
                "note": "This is a test upload using placeholder credentials. No actual upload to YouTube occurred."
            }
        
        try:
            print(f"[YOUTUBE] Starting upload for: {video_file_path}")
            
            # Import Google libraries
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            
            # Create credentials object
            creds = Credentials(
                token=None,  # Will be refreshed
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            # Refresh the credentials
            creds.refresh(Request())
            print(f"[YOUTUBE] Access token obtained: {creds.token[:20]}...")
            
            # Build YouTube service
            youtube = build('youtube', 'v3', credentials=creds)
            
            # Prepare video metadata
            if tags is None:
                tags = ["AI", "Generated", "Shorts", "Video"]
            
            # Ensure title has #Shorts for proper categorization
            if "#Shorts" not in title:
                title = f"{title} #Shorts"
            
            # Enhance description with hashtags
            enhanced_description = f"{description}\n\n#Shorts #AI #Generated"
            
            # Video metadata
            body = {
                "snippet": {
                    "title": title,
                    "description": enhanced_description,
                    "tags": tags,
                    "categoryId": "22",  # People & Blogs
                    "defaultLanguage": "en"
                },
                "status": {
                    "privacyStatus": "public",  # Change to "unlisted" for testing
                    "selfDeclaredMadeForKids": False
                }
            }
            
            print(f"[YOUTUBE] Uploading video with title: {title}")
            
            # Create media upload object
            media = MediaFileUpload(
                video_file_path,
                chunksize=-1,  # Upload in single request
                resumable=True,
                mimetype="video/mp4"
            )
            
            # Execute upload
            insert_request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            print("[YOUTUBE] Executing upload request...")
            
            # Upload the video
            response = None
            error = None
            retry = 0
            max_retries = 3
            
            while response is None and retry < max_retries:
                try:
                    print(f"[YOUTUBE] Upload attempt {retry + 1}")
                    status, response = insert_request.next_chunk()
                    if response is not None:
                        break
                        
                except Exception as upload_error:
                    print(f"[YOUTUBE] Upload error on attempt {retry + 1}: {upload_error}")
                    retry += 1
                    if retry >= max_retries:
                        raise upload_error
                    import time
                    time.sleep(2)
            
            if response is None:
                return {
                    "success": False,
                    "error": "Upload failed - no response received after retries"
                }
            
            # Extract video information
            video_id = response.get("id")
            if not video_id:
                return {
                    "success": False,
                    "error": "Upload completed but no video ID received"
                }
            
            # Generate URLs
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            shorts_url = f"https://www.youtube.com/shorts/{video_id}"
            
            print(f"[YOUTUBE] ✅ SUCCESS! Video uploaded:")
            print(f"[YOUTUBE] Video ID: {video_id}")
            print(f"[YOUTUBE] YouTube URL: {youtube_url}")
            print(f"[YOUTUBE] Shorts URL: {shorts_url}")
            
            return {
                "success": True,
                "video_id": video_id,
                "youtube_url": youtube_url,
                "shorts_url": shorts_url,
                "title": response.get("snippet", {}).get("title", title),
                "upload_time": datetime.now().isoformat(),
                "privacy_status": response.get("status", {}).get("privacyStatus", "public")
            }
            
        except Exception as e:
            print(f"[YOUTUBE] ❌ ERROR: Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"YouTube upload failed: {str(e)}"
            }
    
    def _direct_upload(self, access_token: str, video_file_path: str, metadata: dict) -> Dict[str, Any]:
        """
        Alternative direct upload method using multipart form
        """
        
        try:
            import requests_toolbelt
            from requests_toolbelt.multipart.encoder import MultipartEncoder
            
            # Prepare multipart data
            with open(video_file_path, 'rb') as video_file:
                multipart_data = MultipartEncoder(
                    fields={
                        'snippet': json.dumps(metadata['snippet']),
                        'status': json.dumps(metadata['status']),
                        'media': ('video.mp4', video_file, 'video/mp4')
                    }
                )
                
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': multipart_data.content_type
                }
                
                response = requests.post(
                    'https://www.googleapis.com/youtube/v3/videos?part=snippet,status',
                    data=multipart_data,
                    headers=headers
                )
            
            if response.status_code == 200:
                result_data = response.json()
                video_id = result_data.get("id")
                
                return {
                    "success": True,
                    "video_id": video_id,
                    "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
                    "shorts_url": f"https://www.youtube.com/shorts/{video_id}",
                    "title": result_data.get("snippet", {}).get("title"),
                    "upload_time": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Direct upload failed with status {response.status_code}: {response.text}"
                }
                
        except ImportError:
            return {
                "success": False,
                "error": "requests-toolbelt not installed. Please run: pip install requests-toolbelt"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Direct upload failed: {str(e)}"
            }
    
    def check_quota_status(self) -> Dict[str, Any]:
        """
        Check YouTube API quota status
        """
        
        if not self.configured:
            return {"error": "Not configured"}
        
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {"error": "Failed to get access token"}
            
            # Make a simple API call to check quota
            response = requests.get(
                "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "YouTube API access is working",
                    "quota_status": "OK"
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "YouTube API quota exceeded or access denied",
                    "quota_status": "EXCEEDED"
                }
            else:
                return {
                    "success": False,
                    "error": f"API check failed with status {response.status_code}",
                    "quota_status": "ERROR"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Quota check failed: {str(e)}",
                "quota_status": "ERROR"
            }

def test_youtube_upload():
    """Test YouTube upload functionality"""
    
    uploader = YouTubeUploader()
    
    # Check configuration
    if not uploader.configured:
        print("YouTube uploader not configured")
        print("   Please set these environment variables in .env:")
        print("   - GOOGLE_CLIENT_ID")
        print("   - GOOGLE_CLIENT_SECRET") 
        print("   - YOUTUBE_REFRESH_TOKEN")
        return
    
    # Check quota status
    quota_result = uploader.check_quota_status()
    print(f"Quota check: {quota_result}")
    
    if not quota_result.get("success"):
        print("YouTube API access issues")
        return
    
    print("YouTube uploader is ready for automatic uploads")

if __name__ == "__main__":
    test_youtube_upload()