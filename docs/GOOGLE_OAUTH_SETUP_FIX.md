# 🔧 Fix Google OAuth Sign-In Issues

## Most Common Issue: Domain Authorization

Your OAuth client needs to authorize `localhost:3000` (your frontend domain).

### 1. Check OAuth Client Settings

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Select your project

2. **Go to Credentials**
   - APIs & Services > Credentials
   - Find your OAuth Client: `47528001738-nrkn3t5vq362avjsfdit92k32i3e40iu.apps.googleusercontent.com`
   - Click on it to edit

3. **Check Authorized JavaScript Origins**
   Make sure these are added:
   ```
   http://localhost:3000
   https://localhost:3000
   ```

4. **Check Authorized Redirect URIs** (if any)
   Add:
   ```
   http://localhost:3000
   ```

### 2. Check OAuth Consent Screen

1. **Go to OAuth Consent Screen**
   - APIs & Services > OAuth consent screen

2. **Check Scopes**
   Make sure you have:
   ```
   https://www.googleapis.com/auth/youtube.upload
   ```

3. **Check Test Users** (if app is in testing mode)
   - Add your Gmail account to test users
   - Or publish the app to production

### 3. Enable Required APIs

Make sure these APIs are enabled:
- YouTube Data API v3
- Google+ API (legacy, but sometimes needed)

### 4. Common Error Messages

**"popup_closed_by_user"**
- User closed the popup manually
- Usually not a setup issue

**"access_denied"** 
- OAuth consent screen not configured
- App not published and user not in test users
- Missing required scopes

**"invalid_client"**
- Wrong client ID
- Domain not authorized

**"redirect_uri_mismatch"**
- localhost:3000 not in authorized origins

## 5. Debug Steps

1. **Use Debug Tool** (now on your page)
   - Click "Run Diagnostics" 
   - Check for any red error messages
   - Note the exact error details

2. **Check Browser Console**
   - Open DevTools (F12)
   - Look for JavaScript errors
   - Check Network tab for failed requests

3. **Test with Simple OAuth**
   - Use the debug tool's "Test Sign In" button
   - This will show the exact Google error

## 6. Quick Fix Checklist

✅ **Client ID is correct**: `47528001738-nrkn3t5vq362avjsfdit92k32i3e40iu.apps.googleusercontent.com`
✅ **Domain authorized**: `http://localhost:3000` in JavaScript origins  
✅ **YouTube scope added**: `https://www.googleapis.com/auth/youtube.upload`
✅ **YouTube API enabled**: YouTube Data API v3
✅ **User authorized**: Added to test users OR app published

Most issues are fixed by adding `http://localhost:3000` to the authorized JavaScript origins!