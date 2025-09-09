'use client';

import { useState, useRef, useEffect } from 'react';
import ClientSideYouTubeUploader from './ClientSideYouTubeUploader';
import ProgressBar from './ProgressBar';

export default function CustomVideoPage() {
  const [formData, setFormData] = useState({
    topic: '',
    script_length: 'medium',
    voice: 'alloy',
    width: 1024,
    height: 576,
    fps: 24,
    img_style_prompt: 'cinematic, professional, high quality',
    include_dialogs: true,
    use_different_voices: true,
    add_captions: true,
    add_title_card: true,
    add_end_card: true,
    language: 'en',
    voice_speed: 1.0
  });

  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [r2VideoUrl, setR2VideoUrl] = useState(null);
  const [r2FileName, setR2FileName] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [youtubeVideo, setYoutubeVideo] = useState(null);
  const [showYouTubeUploader, setShowYouTubeUploader] = useState(false);

  const pollIntervalRef = useRef(null);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (type === 'number' ? parseFloat(value) || 0 : value)
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
      const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/generate-advanced-video`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();
      
      if (response.ok) {
        setJobId(data.job_id);
      } else {
        throw new Error(data.error || 'Failed to start video generation');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error: ' + error.message);
      setIsGenerating(false);
    }
  };

  const startPolling = (id) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
    
    pollIntervalRef.current = setInterval(async () => {
      try {
        const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${apiBase}/jobs/${id}/status`);
        const data = await response.json();
        
        setStatus(data);

        if (data.status === 'completed') {
          clearInterval(pollIntervalRef.current);
          setIsGenerating(false);
          uploadVideoToR2(id);
        } else if (data.status === 'failed') {
          clearInterval(pollIntervalRef.current);
          setIsGenerating(false);
          alert('Video generation failed: ' + data.error);
        }
      } catch (error) {
        console.error('Error checking status:', error);
      }
    }, 1500);
  };

  const uploadVideoToR2 = async (id) => {
    try {
      console.log('Starting R2 upload for job:', id);
      setIsUploading(true);
      
      const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/jobs/${id}/download`);
      if (!response.ok) throw new Error('Failed to download video');
      
      const blob = await response.blob();
      const fileName = `video-${id}-${Date.now()}.mp4`;
      
      const formData = new FormData();
      formData.append('file', blob, fileName);
      formData.append('fileName', fileName);
      
      const uploadResponse = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      
      if (uploadResponse.ok) {
        const result = await uploadResponse.json();
        setR2VideoUrl(result.publicUrl);
        setR2FileName(result.fileName);
        
        console.log('R2 upload successful, triggering cleanup...');
        await triggerCleanupAfterUpload(id);
      } else {
        const errorText = await uploadResponse.text();
        throw new Error('R2 upload failed: ' + errorText);
      }
    } catch (error) {
      console.error('Upload to R2 failed:', error);
      alert('Failed to upload video to cloud storage: ' + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  const triggerCleanupAfterUpload = async (jobId) => {
    try {
      console.log(`Triggering cleanup for job ${jobId}...`);
      
      const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const cleanupResponse = await fetch(`${apiBase}/jobs/${jobId}/cleanup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          keep_final_video: true
        })
      });

      if (cleanupResponse.ok) {
        const result = await cleanupResponse.json();
        console.log('Cleanup completed successfully:', result.message);
      } else {
        const errorText = await cleanupResponse.text();
        console.warn('Cleanup failed (non-critical):', errorText);
      }
    } catch (error) {
      console.warn('Cleanup request failed (non-critical):', error.message);
    }
  };

  const handleDownload = () => {
    if (jobId && status?.status === 'completed') {
      const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      window.open(`${apiBase}/jobs/${jobId}/download`, '_blank');
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

  const handleYouTubeUploadClick = () => {
    if (!r2VideoUrl && (!jobId || status?.status !== 'completed')) {
      alert('No video available to upload');
      return;
    }
    setShowYouTubeUploader(true);
  };

  const handleYouTubeUploadSuccess = (result) => {
    setYoutubeVideo({
      title: result.title,
      videoId: result.videoId,
      youtubeUrl: result.youtubeUrl,
      shortsUrl: result.shortsUrl,
      manual: false
    });

    setShowYouTubeUploader(false);
    alert(`✅ Video uploaded to YouTube successfully!\n\n🎬 YouTube URL: ${result.shortsUrl}\n📺 Video ID: ${result.videoId}`);
  };

  const handleYouTubeUploadError = (error) => {
    console.error('YouTube upload failed:', error);
    alert('Failed to upload to YouTube: ' + error);
  };

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const getProgressStages = () => {
    if (!status) return [];
    
    const stages = [
      { name: 'Script Generation', progress: 0 },
      { name: 'Audio Generation', progress: 0 },
      { name: 'Image Generation', progress: 0 },
      { name: 'Video Creation', progress: 0 },
      { name: 'Final Processing', progress: 0 }
    ];

    const totalProgress = status.progress || 0;
    
    if (totalProgress >= 20) stages[0].progress = 100;
    if (totalProgress >= 40) stages[1].progress = 100;
    if (totalProgress >= 60) stages[2].progress = 100;
    if (totalProgress >= 80) stages[3].progress = 100;
    if (totalProgress >= 100) stages[4].progress = 100;

    return stages;
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">Custom Video Generation</h2>
        <p className="text-gray-400 mt-1">Create personalized videos with custom settings</p>
      </div>

      {/* Video Generation Form */}
      <div className="glass rounded-2xl p-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Topic */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Topic *
              </label>
              <textarea
                name="topic"
                value={formData.topic}
                onChange={handleInputChange}
                placeholder="Enter your video topic..."
                className="w-full p-3 input-dark rounded-lg resize-none"
                rows="3"
                required
              />
            </div>

            {/* Script Length */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Script Length
              </label>
              <select
                name="script_length"
                value={formData.script_length}
                onChange={handleInputChange}
                className="w-full p-3 input-dark rounded-lg"
              >
                <option value="short">Short (30-60 seconds)</option>
                <option value="medium">Medium (60-120 seconds)</option>
                <option value="long">Long (120-180 seconds)</option>
              </select>
            </div>

            {/* Voice */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Voice
              </label>
              <select
                name="voice"
                value={formData.voice}
                onChange={handleInputChange}
                className="w-full p-3 input-dark rounded-lg"
              >
                <option value="alloy">Alloy</option>
                <option value="echo">Echo</option>
                <option value="fable">Fable</option>
                <option value="onyx">Onyx</option>
                <option value="nova">Nova</option>
                <option value="shimmer">Shimmer</option>
              </select>
            </div>

            {/* Video Dimensions */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
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
                className="w-full p-3 input-dark rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
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
                className="w-full p-3 input-dark rounded-lg"
              />
            </div>

            {/* FPS */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                FPS
              </label>
              <select
                name="fps"
                value={formData.fps}
                onChange={handleInputChange}
                className="w-full p-3 input-dark rounded-lg"
              >
                <option value={24}>24 FPS</option>
                <option value={30}>30 FPS</option>
                <option value={60}>60 FPS</option>
              </select>
            </div>

            {/* Image Style Prompt */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Image Style Prompt
              </label>
              <input
                type="text"
                name="img_style_prompt"
                value={formData.img_style_prompt}
                onChange={handleInputChange}
                placeholder="cinematic, professional, high quality"
                className="w-full p-3 input-dark rounded-lg"
              />
            </div>

            {/* Voice Speed */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
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
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Language */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Language
              </label>
              <select
                name="language"
                value={formData.language}
                onChange={handleInputChange}
                className="w-full p-3 input-dark rounded-lg"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="it">Italian</option>
                <option value="pt">Portuguese</option>
              </select>
            </div>
          </div>

          {/* Advanced Options */}
          <div className="border-t border-gray-600 pt-6">
            <h3 className="text-lg font-semibold text-white mb-4">Advanced Options</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="include_dialogs"
                  checked={formData.include_dialogs}
                  onChange={handleInputChange}
                  className="rounded"
                />
                <span className="text-gray-300">Include Dialogs</span>
              </label>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="use_different_voices"
                  checked={formData.use_different_voices}
                  onChange={handleInputChange}
                  className="rounded"
                />
                <span className="text-gray-300">Use Different Voices</span>
              </label>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="add_captions"
                  checked={formData.add_captions}
                  onChange={handleInputChange}
                  className="rounded"
                />
                <span className="text-gray-300">Add Captions</span>
              </label>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="add_title_card"
                  checked={formData.add_title_card}
                  onChange={handleInputChange}
                  className="rounded"
                />
                <span className="text-gray-300">Add Title Card</span>
              </label>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="add_end_card"
                  checked={formData.add_end_card}
                  onChange={handleInputChange}
                  className="rounded"
                />
                <span className="text-gray-300">Add End Card</span>
              </label>
            </div>
          </div>

          <div className="flex justify-center">
            <button
              type="submit"
              disabled={isGenerating}
              className="px-8 py-3 btn-primary rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all"
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
      </div>

      {/* Progress Display */}
      {jobId && (
        <div className="glass rounded-2xl p-6">
          <h3 className="text-xl font-semibold mb-6 text-white">Generation Progress</h3>
          
          <ProgressBar 
            jobId={jobId}
            autoStart={true}
            showDetails={true}
            onComplete={(data) => {
              setStatus(data);
              setIsGenerating(false);
              uploadVideoToR2(jobId);
            }}
            onError={(error) => {
              setIsGenerating(false);
              alert('Video generation failed: ' + error);
            }}
          />
          
          {status?.status === 'completed' && (
            <div className="mt-6 flex flex-wrap justify-center gap-4">
              <button
                onClick={handleDownload}
                className="px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-all flex items-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span>Download</span>
              </button>
              
              <button
                onClick={handleYouTubeUploadClick}
                className="px-6 py-3 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700 transition-all flex items-center space-x-2"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
                <span>Upload to YouTube</span>
              </button>

              {isUploading && (
                <div className="flex items-center space-x-2 px-6 py-3 bg-blue-900/20 text-blue-400 border border-blue-500/30 rounded-lg">
                  <div className="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                  <span>Uploading to Cloud...</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Video Display */}
      {r2VideoUrl && (
        <div className="glass rounded-2xl p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold text-white">Your Generated Video</h3>
            <button
              onClick={handleDeleteFromR2}
              className="px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-all flex items-center space-x-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <span>Delete</span>
            </button>
          </div>
          
          <div className="relative rounded-lg overflow-hidden bg-black">
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
              className="text-blue-400 hover:text-blue-300 transition-colors"
            >
              Open in new tab ↗
            </a>
          </div>
        </div>
      )}

      {/* YouTube Upload Dialog */}
      {showYouTubeUploader && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-lg w-full mx-4 border border-gray-600 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <div className="bg-red-100 rounded-full p-2 mr-3">
                  <svg className="w-6 h-6 text-red-600" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-white">Upload to YouTube</h3>
              </div>
              <button
                onClick={() => setShowYouTubeUploader(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <ClientSideYouTubeUploader
              videoUrl={r2VideoUrl || (jobId ? `${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/jobs/${jobId}/download` : null)}
              videoTitle={`AI Generated: ${formData.topic || 'Amazing Content'}`}
              onUploadSuccess={handleYouTubeUploadSuccess}
              onUploadError={handleYouTubeUploadError}
            />
          </div>
        </div>
      )}

      {/* YouTube Success */}
      {youtubeVideo && (
        <div className="glass rounded-2xl p-6 border border-green-500/20">
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
              
              <button
                onClick={() => navigator.clipboard.writeText(youtubeVideo.youtubeUrl)}
                className="px-4 py-2 btn-secondary rounded-lg transition-colors flex items-center space-x-2"
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
  );
}