'use client';

import { useState, useEffect } from 'react';

export default function Home() {
  const [formData, setFormData] = useState({
    topic: '',
    style: 'informative',
    num_segments: 5,
    duration_per_segment: 4.0,
    language: 'en',
    voice_speed: 1.0,
    width: 1024,
    height: 576,
    fps: 24,
    image_model: 'flux'
  });

  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [r2VideoUrl, setR2VideoUrl] = useState(null);
  const [r2FileName, setR2FileName] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [youtubeUser, setYoutubeUser] = useState(null);
  const [youtubeVideo, setYoutubeVideo] = useState(null);
  const [isUploadingToYoutube, setIsUploadingToYoutube] = useState(false);

  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.topic.trim()) {
      alert('Please enter a topic');
      return;
    }

    setIsGenerating(true);
    setStatus(null);
    setJobId(null);

    try {
      const response = await fetch('http://localhost:8000/generate-video', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();
      
      if (response.ok) {
        setJobId(data.job_id);
        pollJobStatus(data.job_id);
      } else {
        throw new Error(data.error || 'Failed to start video generation');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error: ' + error.message);
      setIsGenerating(false);
    }
  };

  const pollJobStatus = async (id) => {
    const poll = async () => {
      try {
        const response = await fetch(`http://localhost:8000/jobs/${id}/status`);
        const data = await response.json();
        
        setStatus(data);

        if (data.status === 'completed') {
          setIsGenerating(false);
          // Auto-upload to R2 when video is completed
          uploadVideoToR2(id);
        } else if (data.status === 'failed') {
          setIsGenerating(false);
          alert('Video generation failed: ' + data.error);
        } else if (data.status === 'processing' || data.status === 'queued') {
          setTimeout(poll, 2000);
        }
      } catch (error) {
        console.error('Error checking status:', error);
        setTimeout(poll, 5000);
      }
    };
    
    poll();
  };

  const uploadVideoToR2 = async (id) => {
    try {
      console.log('Starting R2 upload for job:', id);
      setIsUploading(true);
      
      // Download video from Flask backend
      console.log('Downloading video from Flask backend...');
      const response = await fetch(`http://localhost:8000/jobs/${id}/download`);
      if (!response.ok) throw new Error('Failed to download video');
      
      const blob = await response.blob();
      const fileName = `video-${id}-${Date.now()}.mp4`;
      console.log('Downloaded video blob, size:', blob.size, 'fileName:', fileName);
      
      // Upload to R2 via Next.js API
      const formData = new FormData();
      formData.append('file', blob, fileName);
      formData.append('fileName', fileName);
      
      console.log('Uploading to R2...');
      const uploadResponse = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      
      console.log('Upload response status:', uploadResponse.status);
      
      if (uploadResponse.ok) {
        const result = await uploadResponse.json();
        console.log('Upload result:', result);
        setR2VideoUrl(result.publicUrl);
        setR2FileName(result.fileName);
        console.log('Video uploaded to R2:', result.publicUrl);
      } else {
        const errorText = await uploadResponse.text();
        console.error('Upload failed:', errorText);
        throw new Error('R2 upload failed: ' + errorText);
      }
    } catch (error) {
      console.error('Upload to R2 failed:', error);
      alert('Failed to upload video to cloud storage: ' + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownload = () => {
    if (jobId && status?.status === 'completed') {
      window.open(`http://localhost:8000/jobs/${jobId}/download`, '_blank');
    }
  };

  const handleDeleteFromR2 = async () => {
    if (!r2FileName) return;
    
    try {
      const response = await fetch(`/api/delete?fileName=${r2FileName}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        setR2VideoUrl(null);
        setR2FileName(null);
        alert('Video deleted from cloud storage');
      } else {
        throw new Error('Delete failed');
      }
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Failed to delete video: ' + error.message);
    }
  };

  // YouTube Authentication
  const handleYouTubeAuth = async () => {
    try {
      const response = await fetch('/api/youtube/auth?action=login');
      const data = await response.json();
      
      if (data.authUrl) {
        // Open popup window for OAuth
        window.open(data.authUrl, 'youtube-auth', 'width=500,height=600');
        
        // Listen for auth completion
        const checkAuth = setInterval(() => {
          const userCookie = document.cookie
            .split('; ')
            .find(row => row.startsWith('youtube_user='));
            
          if (userCookie) {
            const userData = JSON.parse(decodeURIComponent(userCookie.split('=')[1]));
            setYoutubeUser(userData);
            clearInterval(checkAuth);
          }
        }, 1000);
        
        // Stop checking after 2 minutes
        setTimeout(() => clearInterval(checkAuth), 120000);
      }
    } catch (error) {
      console.error('YouTube auth failed:', error);
      alert('YouTube authentication failed: ' + error.message);
    }
  };

  // YouTube Upload
  const handleYouTubeUpload = async () => {
    if (!jobId || !status?.status === 'completed') {
      alert('No video available to upload');
      return;
    }

    if (!youtubeUser) {
      alert('Please authenticate with YouTube first');
      return;
    }

    try {
      setIsUploadingToYoutube(true);
      
      const formData = new FormData();
      formData.append('jobId', jobId);
      formData.append('title', `AI Generated Video - ${formData.topic || 'Amazing Content'}`);
      formData.append('description', `Generated with AI Video Generator\nTopic: ${formData.topic || 'AI Content'}\n\n#Shorts #AI #Generated`);
      formData.append('tags', 'AI,Shorts,Generated,Video,Artificial Intelligence');

      const response = await fetch('/api/youtube/upload', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      
      if (result.success) {
        setYoutubeVideo(result);
        alert('Video uploaded to YouTube successfully!');
      } else {
        throw new Error(result.error || 'Upload failed');
      }
    } catch (error) {
      console.error('YouTube upload failed:', error);
      alert('YouTube upload failed: ' + error.message);
    } finally {
      setIsUploadingToYoutube(false);
    }
  };

  // Check for YouTube auth on component mount
  useEffect(() => {
    const userCookie = document.cookie
      .split('; ')
      .find(row => row.startsWith('youtube_user='));
      
    if (userCookie) {
      try {
        const userData = JSON.parse(decodeURIComponent(userCookie.split('=')[1]));
        setYoutubeUser(userData);
      } catch (error) {
        console.error('Error parsing YouTube user data:', error);
      }
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-4">
            AI Video Generator
          </h1>
          <p className="text-gray-300 text-lg">
            Create stunning videos with AI-powered scripts and visuals
          </p>
        </div>

        <div className="bg-white/10 backdrop-blur-lg rounded-2xl border border-white/20 shadow-2xl p-8">
          {/* YouTube User Status */}
          {youtubeUser && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
              <div className="flex items-center space-x-3">
                <img 
                  src={youtubeUser.picture} 
                  alt={youtubeUser.name}
                  className="w-10 h-10 rounded-full"
                />
                <div>
                  <p className="text-white font-medium">Connected to YouTube</p>
                  <p className="text-gray-400 text-sm">{youtubeUser.name}</p>
                </div>
                <div className="ml-auto">
                  <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Topic */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-white mb-3">
                  Topic *
                </label>
                <textarea
                  name="topic"
                  value={formData.topic}
                  onChange={handleInputChange}
                  placeholder="Enter your video topic..."
                  className="w-full p-4 bg-white/5 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-400 focus:border-purple-400 transition-all duration-200"
                  rows="3"
                  required
                />
              </div>

              {/* Style */}
              <div>
                <label className="block text-sm font-medium text-white mb-3">
                  Style
                </label>
                <select
                  name="style"
                  value={formData.style}
                  onChange={handleInputChange}
                  className="w-full p-4 bg-white/5 border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-purple-400 focus:border-purple-400 transition-all duration-200"
                >
                  <option value="informative">Informative</option>
                  <option value="educational">Educational</option>
                  <option value="entertainment">Entertainment</option>
                  <option value="documentary">Documentary</option>
                  <option value="tutorial">Tutorial</option>
                </select>
              </div>

              {/* Number of Segments */}
              <div>
                <label className="block text-sm font-medium text-white mb-3">
                  Number of Segments
                </label>
                <input
                  type="number"
                  name="num_segments"
                  value={formData.num_segments}
                  onChange={handleInputChange}
                  min="1"
                  max="20"
                  className="w-full p-4 bg-white/5 border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-purple-400 focus:border-purple-400 transition-all duration-200"
                />
              </div>

              {/* Duration per Segment */}
              <div>
                <label className="block text-sm font-medium text-white mb-3">
                  Duration per Segment (seconds)
                </label>
                <input
                  type="number"
                  name="duration_per_segment"
                  value={formData.duration_per_segment}
                  onChange={handleInputChange}
                  min="1"
                  max="10"
                  step="0.5"
                  className="w-full p-4 bg-white/5 border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-purple-400 focus:border-purple-400 transition-all duration-200"
                />
              </div>

              {/* Language */}
              <div>
                <label className="block text-sm font-medium text-white mb-3">
                  Language
                </label>
                <select
                  name="language"
                  value={formData.language}
                  onChange={handleInputChange}
                  className="w-full p-4 bg-white/5 border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-purple-400 focus:border-purple-400 transition-all duration-200"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="it">Italian</option>
                  <option value="pt">Portuguese</option>
                </select>
              </div>

              {/* Voice Speed */}
              <div>
                <label className="block text-sm font-medium text-white mb-3">
                  Voice Speed: {formData.voice_speed}x
                </label>
                <input
                  type="range"
                  name="voice_speed"
                  value={formData.voice_speed}
                  onChange={handleInputChange}
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer slider"
                  style={{
                    background: `linear-gradient(to right, rgb(168 85 247) 0%, rgb(168 85 247) ${(formData.voice_speed - 0.5) / 1.5 * 100}%, rgb(255 255 255 / 0.1) ${(formData.voice_speed - 0.5) / 1.5 * 100}%, rgb(255 255 255 / 0.1) 100%)`
                  }}
                />
              </div>

              {/* Video Dimensions */}
              <div>
                <label className="block text-sm font-medium text-white mb-3">
                  Width
                </label>
                <input
                  type="number"
                  name="width"
                  value={formData.width}
                  onChange={handleInputChange}
                  min="480"
                  max="1920"
                  step="16"
                  className="w-full p-4 bg-white/5 border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-purple-400 focus:border-purple-400 transition-all duration-200"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-3">
                  Height
                </label>
                <input
                  type="number"
                  name="height"
                  value={formData.height}
                  onChange={handleInputChange}
                  min="360"
                  max="1080"
                  step="16"
                  className="w-full p-4 bg-white/5 border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-purple-400 focus:border-purple-400 transition-all duration-200"
                />
              </div>

              {/* FPS */}
              <div>
                <label className="block text-sm font-medium text-white mb-3">
                  FPS
                </label>
                <select
                  name="fps"
                  value={formData.fps}
                  onChange={handleInputChange}
                  className="w-full p-4 bg-white/5 border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-purple-400 focus:border-purple-400 transition-all duration-200"
                >
                  <option value={24}>24 FPS</option>
                  <option value={30}>30 FPS</option>
                  <option value={60}>60 FPS</option>
                </select>
              </div>

              {/* Image Model */}
              <div>
                <label className="block text-sm font-medium text-white mb-3">
                  Image Model
                </label>
                <select
                  name="image_model"
                  value={formData.image_model}
                  onChange={handleInputChange}
                  className="w-full p-4 bg-white/5 border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-purple-400 focus:border-purple-400 transition-all duration-200"
                >
                  <option value="flux">Flux</option>
                  <option value="dall-e">DALL-E</option>
                  <option value="stable-diffusion">Stable Diffusion</option>
                </select>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-center mt-8">
              <button
                type="submit"
                disabled={isGenerating}
                className="px-12 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-xl hover:from-purple-600 hover:to-pink-600 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 disabled:transform-none shadow-lg"
              >
                {isGenerating ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Generating Video...</span>
                  </div>
                ) : (
                  'Generate Video'
                )}
              </button>
            </div>
          </form>

          {/* Status Display */}
          {status && (
            <div className="mt-8 p-6 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/20">
              <h3 className="text-xl font-semibold mb-4 text-white">Generation Status</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Status:</span>
                  <span className={`font-medium px-3 py-1 rounded-full text-sm ${
                    status.status === 'completed' 
                      ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                    status.status === 'failed' 
                      ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                      'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  }`}>
                    {status.status}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Progress:</span>
                  <span className="text-white font-medium">{status.progress}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-3 overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-full rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${status.progress}%` }}
                  ></div>
                </div>
                <div className="mt-3">
                  <span className="text-sm text-gray-400 italic">{status.message}</span>
                </div>
                
                {status.status === 'completed' && (
                  <div className="mt-6 space-y-4">
                    <div className="flex justify-center space-x-4">
                      <button
                        onClick={handleDownload}
                        className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-xl hover:from-green-600 hover:to-emerald-600 transition-all duration-200 transform hover:scale-105 shadow-lg"
                      >
                        <div className="flex items-center space-x-2">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <span>Download</span>
                        </div>
                      </button>
                      
                      {/* YouTube Upload Section */}
                      {!youtubeUser ? (
                        <button
                          onClick={handleYouTubeAuth}
                          className="px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white font-semibold rounded-xl hover:from-red-600 hover:to-red-700 transition-all duration-200 transform hover:scale-105 shadow-lg"
                        >
                          <div className="flex items-center space-x-2">
                            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                            </svg>
                            <span>Connect YouTube</span>
                          </div>
                        </button>
                      ) : (
                        <button
                          onClick={handleYouTubeUpload}
                          disabled={isUploadingToYoutube}
                          className="px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white font-semibold rounded-xl hover:from-red-600 hover:to-red-700 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 disabled:transform-none shadow-lg"
                        >
                          {isUploadingToYoutube ? (
                            <div className="flex items-center space-x-2">
                              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                              <span>Uploading to YouTube...</span>
                            </div>
                          ) : (
                            <div className="flex items-center space-x-2">
                              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                              </svg>
                              <span>Upload to YouTube</span>
                            </div>
                          )}
                        </button>
                      )}

                      {isUploading && (
                        <div className="flex items-center space-x-2 px-6 py-3 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-xl">
                          <div className="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                          <span>Uploading to Cloud...</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Video Display Section */}
          {r2VideoUrl && (
            <div className="mt-8 p-6 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/20">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-semibold text-white">Your Generated Video</h3>
                <button
                  onClick={handleDeleteFromR2}
                  className="px-4 py-2 bg-gradient-to-r from-red-500 to-pink-500 text-white font-medium rounded-lg hover:from-red-600 hover:to-pink-600 transition-all duration-200 transform hover:scale-105"
                >
                  <div className="flex items-center space-x-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    <span>Delete</span>
                  </div>
                </button>
              </div>
              
              <div className="relative rounded-xl overflow-hidden bg-black">
                <video
                  src={r2VideoUrl}
                  controls
                  className="w-full h-auto max-h-96 object-contain"
                  preload="metadata"
                >
                  Your browser does not support the video tag.
                </video>
              </div>
              
              <div className="mt-4 flex justify-between items-center text-sm text-gray-400">
                <span>Stored in Cloudflare R2</span>
                <a
                  href={r2VideoUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-purple-400 hover:text-purple-300 transition-colors"
                >
                  Open in new tab ↗
                </a>
              </div>
            </div>
          )}

          {/* YouTube Video Result */}
          {youtubeVideo && (
            <div className="mt-8 p-6 bg-red-500/10 backdrop-blur-sm rounded-2xl border border-red-500/20">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-semibold text-white">Uploaded to YouTube!</h3>
                <div className="flex items-center space-x-2 text-green-400">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-sm">Success</span>
                </div>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="text-white font-medium mb-2">{youtubeVideo.title}</h4>
                  <p className="text-gray-400 text-sm">Video ID: {youtubeVideo.videoId}</p>
                </div>
                
                <div className="flex flex-wrap gap-3">
                  <a
                    href={youtubeVideo.youtubeUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                    </svg>
                    <span>Watch on YouTube</span>
                  </a>
                  
                  <a
                    href={youtubeVideo.shortsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700 transition-colors flex items-center space-x-2"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    <span>YouTube Shorts</span>
                  </a>
                  
                  <button
                    onClick={() => navigator.clipboard.writeText(youtubeVideo.youtubeUrl)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center space-x-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span>Copy Link</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
