#!/usr/bin/env python3
"""
Simple script to get YouTube refresh token for direct uploads
Run this once to get the refresh token, then add it to your .env file
"""

import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow

# Load environment variables
load_dotenv()

def get_youtube_refresh_token():
    """Get YouTube refresh token for direct uploads"""
    
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env file")
        return None
    
    # Create OAuth flow for desktop application
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/youtube.upload'],
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )
    
    # Get authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',  # Important: gets refresh token
        prompt='consent'        # Important: ensures refresh token
    )
    
    print("YouTube Token Generator")
    print("=" * 50)
    print()
    print("1. Open this URL in your browser:")
    print(f"   {auth_url}")
    print()
    print("2. Authorize the application")
    print("3. Google will show you an authorization code")
    print("4. Copy the authorization code (NOT the full URL)")
    print()
    
    # Get authorization code from user
    auth_code = input("5. Paste the authorization code here: ").strip()
    
    try:
        if not auth_code:
            print("Error: No authorization code provided")
            return None
        
        # Exchange code for tokens
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        
        if credentials.refresh_token:
            print()
            print("SUCCESS! Here's your refresh token:")
            print("=" * 50)
            print(f"YOUTUBE_REFRESH_TOKEN={credentials.refresh_token}")
            print("=" * 50)
            print()
            print("Add this line to your .env file:")
            print(f"   YOUTUBE_REFRESH_TOKEN={credentials.refresh_token}")
            print()
            print("Now you can upload directly to YouTube!")
            
            return credentials.refresh_token
        else:
            print("Error: No refresh token received. Make sure to use access_type='offline' and prompt='consent'")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    try:
        get_youtube_refresh_token()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"\nError: {e}")