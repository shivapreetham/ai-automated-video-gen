'use client';

import { useState, useEffect } from 'react';

export default function DataManager() {
  const [videos, setVideos] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedVideos, setSelectedVideos] = useState(new Set());
  const [uploadProgress, setUploadProgress] = useState({});

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    setIsLoading(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      
      // Fetch from multiple sources
      const [completedVideos, cloudflareVideos] = await Promise.all([
        fetch(`${apiBase}/agentic/completed-videos?limit=50`).then(r => r.json()),
        fetch(`${apiBase}/cloudflare/list-videos`).then(r => r.json())
      ]);

      const allVideos = [
        ...(completedVideos.completed_videos || []).map(v => ({
          ...v,
          source: 'local',
          status: 'completed'
        })),
        ...(cloudflareVideos.videos || []).map(v => ({
          ...v,
          source: 'cloudflare',
          status: 'uploaded'
        }))
      ];

      setVideos(allVideos);
    } catch (error) {
      console.error('Error fetching videos:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleVideoSelection = (videoId) => {
    const newSelected = new Set(selectedVideos);
    if (newSelected.has(videoId)) {
      newSelected.delete(videoId);
    } else {
      newSelected.add(videoId);
    }
    setSelectedVideos(newSelected);
  };

  const selectAll = () => {
    setSelectedVideos(new Set(videos.map(v => v.job_id || v.id)));
  };

  const deselectAll = () => {
    setSelectedVideos(new Set());
  };

  const deleteSelected = async () => {
    if (selectedVideos.size === 0) return;
    
    if (!confirm(`Delete ${selectedVideos.size} selected videos? This action cannot be undone.`)) {
      return;
    }

    const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const deletePromises = Array.from(selectedVideos).map(async (videoId) => {
      const video = videos.find(v => (v.job_id || v.id) === videoId);
      if (video?.source === 'cloudflare') {
        return fetch(`${apiBase}/cloudflare/delete-video`, {
          method: 'DELETE',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ video_id: videoId })
        });
      } else {
        return fetch(`${apiBase}/jobs/${videoId}/delete`, {
          method: 'DELETE'
        });
      }
    });

    try {
      await Promise.all(deletePromises);
      await fetchVideos();
      setSelectedVideos(new Set());
      alert(`Successfully deleted ${deletePromises.length} videos`);
    } catch (error) {
      console.error('Error deleting videos:', error);
      alert('Some videos could not be deleted');
    }
  };

  const uploadToCloudflare = async (videoId) => {
    const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    
    setUploadProgress(prev => ({ ...prev, [videoId]: 0 }));
    
    try {
      const response = await fetch(`${apiBase}/upload/video-to-cloudflare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: videoId })
      });

      if (response.ok) {
        setUploadProgress(prev => ({ ...prev, [videoId]: 100 }));
        setTimeout(() => {
          setUploadProgress(prev => {
            const newProgress = { ...prev };
            delete newProgress[videoId];
            return newProgress;
          });
          fetchVideos();
        }, 2000);
        alert('Video uploaded to Cloudflare successfully!');
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadProgress(prev => {
        const newProgress = { ...prev };
        delete newProgress[videoId];
        return newProgress;
      });
      alert('Failed to upload video to Cloudflare');
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-3">
          <div className="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-gray-300">Loading videos...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">Data Management</h2>
          <p className="text-gray-400 mt-1">Manage your generated videos and uploads</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <span className="text-sm text-gray-400">
            {videos.length} total videos
          </span>
          <button
            onClick={fetchVideos}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Bulk Actions */}
      {videos.length > 0 && (
        <div className="glass rounded-2xl p-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-300">
                {selectedVideos.size} selected
              </span>
              <div className="flex space-x-2">
                <button
                  onClick={selectAll}
                  className="px-3 py-1 text-sm bg-gray-700 text-white rounded hover:bg-gray-600"
                >
                  Select All
                </button>
                <button
                  onClick={deselectAll}
                  className="px-3 py-1 text-sm bg-gray-700 text-white rounded hover:bg-gray-600"
                >
                  Clear
                </button>
              </div>
            </div>
            
            {selectedVideos.size > 0 && (
              <button
                onClick={deleteSelected}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <span>Delete Selected</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Videos Grid */}
      {videos.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📹</div>
          <h3 className="text-xl font-semibold text-gray-300 mb-2">No videos found</h3>
          <p className="text-gray-500">Generate your first video to see it here</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {videos.map((video) => {
            const videoId = video.job_id || video.id;
            const isSelected = selectedVideos.has(videoId);
            const isUploading = uploadProgress[videoId] !== undefined;
            
            return (
              <div
                key={videoId}
                className={`video-card glass rounded-xl overflow-hidden cursor-pointer animate-fade-in ${
                  isSelected ? 'ring-2 ring-blue-500' : ''
                }`}
                onClick={() => toggleVideoSelection(videoId)}
              >
                {/* Video Preview */}
                <div className="aspect-video bg-gray-800 relative">
                  {video.thumbnail_url ? (
                    <img
                      src={video.thumbnail_url}
                      alt={video.topic}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </div>
                  )}
                  
                  {/* Selection indicator */}
                  {isSelected && (
                    <div className="absolute top-2 right-2 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                  
                  {/* Source badge */}
                  <div className={`absolute top-2 left-2 px-2 py-1 rounded-full text-xs font-medium ${
                    video.source === 'cloudflare' 
                      ? 'bg-green-600/80 text-green-100' 
                      : 'bg-blue-600/80 text-blue-100'
                  }`}>
                    {video.source === 'cloudflare' ? '☁️ Cloud' : '💻 Local'}
                  </div>
                  
                  {/* Upload progress */}
                  {isUploading && (
                    <div className="absolute bottom-0 left-0 right-0 bg-black/50 p-2">
                      <div className="w-full bg-gray-600 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress[videoId]}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-white mt-1">Uploading...</div>
                    </div>
                  )}
                </div>
                
                {/* Video Info */}
                <div className="p-4">
                  <h3 className="font-semibold text-white text-sm mb-1 line-clamp-2">
                    {video.topic}
                  </h3>
                  
                  <div className="flex items-center justify-between text-xs text-gray-400 mb-3">
                    <span>{video.domain || 'Unknown'}</span>
                    <span>{formatFileSize(video.file_size)}</span>
                  </div>
                  
                  <div className="text-xs text-gray-500 mb-3">
                    {formatDate(video.completed_at || video.created_at)}
                  </div>
                  
                  {/* Actions */}
                  <div className="flex space-x-2">
                    {video.download_url && (
                      <a
                        href={video.download_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 text-center"
                        onClick={(e) => e.stopPropagation()}
                      >
                        View
                      </a>
                    )}
                    
                    {video.source === 'local' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          uploadToCloudflare(videoId);
                        }}
                        disabled={isUploading}
                        className="flex-1 px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50"
                      >
                        {isUploading ? 'Uploading...' : 'Upload'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}