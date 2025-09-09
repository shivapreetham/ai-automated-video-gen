'use client';

import { useState, useEffect, useRef } from 'react';
import ProgressBar from './ProgressBar';

export default function AgenticDashboard() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [queueStatus, setQueueStatus] = useState(null);
  const [cloudflareStatus, setCloudflareStatus] = useState(null);
  const [completedVideos, setCompletedVideos] = useState([]);
  const [activityStream, setActivityStream] = useState(null);
  const [metrics, setMetrics] = useState(null);
  
  // Control states
  const [workersRunning, setWorkersRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Topic generation
  const [topicDomains, setTopicDomains] = useState(['indian_mythology', 'technology', 'science']);
  const [topicsPerDomain, setTopicsPerDomain] = useState(5);
  const [reviewTopics, setReviewTopics] = useState([]);
  const [showTopicReview, setShowTopicReview] = useState(false);
  
  // OAuth management
  const [oauthKey, setOauthKey] = useState('');
  const [uploadPlatform, setUploadPlatform] = useState('youtube');
  
  // Polling
  const pollIntervalRef = useRef(null);
  
  const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  
  useEffect(() => {
    // Start polling when component mounts
    startPolling();
    loadInitialData();
    
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);
  
  const startPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
    
    pollIntervalRef.current = setInterval(() => {
      fetchSystemStatus();
      fetchQueueStatus();
      fetchCloudflareStatus();
    }, 5000); // Poll every 5 seconds
  };
  
  const loadInitialData = async () => {
    await Promise.all([
      fetchSystemStatus(),
      fetchQueueStatus(),
      fetchCloudflareStatus(),
      fetchCompletedVideos(),
      fetchActivityStream(),
      fetchMetrics()
    ]);
  };
  
  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${apiBase}/polling/system-status`);
      const data = await response.json();
      setSystemStatus(data.system_status);
      setWorkersRunning(data.system_status?.health?.workers_running || false);
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };
  
  const fetchQueueStatus = async () => {
    try {
      const response = await fetch(`${apiBase}/agentic/queue-status`);
      const data = await response.json();
      setQueueStatus(data.queue_status);
    } catch (error) {
      console.error('Error fetching queue status:', error);
    }
  };
  
  const fetchCloudflareStatus = async () => {
    try {
      const response = await fetch(`${apiBase}/cloudflare/storage-status`);
      const data = await response.json();
      setCloudflareStatus(data);
    } catch (error) {
      console.error('Error fetching Cloudflare status:', error);
    }
  };
  
  const fetchCompletedVideos = async () => {
    try {
      const response = await fetch(`${apiBase}/agentic/completed-videos?limit=10`);
      const data = await response.json();
      setCompletedVideos(data.completed_videos || []);
    } catch (error) {
      console.error('Error fetching completed videos:', error);
    }
  };
  
  const fetchActivityStream = async () => {
    try {
      const response = await fetch(`${apiBase}/polling/activity-stream`);
      const data = await response.json();
      setActivityStream(data.activity_stream);
    } catch (error) {
      console.error('Error fetching activity stream:', error);
    }
  };
  
  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${apiBase}/polling/metrics`);
      const data = await response.json();
      setMetrics(data.metrics);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };
  
  const startWorkforce = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBase}/agentic/start-workforce`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ num_workers: 1 })
      });
      
      const data = await response.json();
      if (data.success) {
        setWorkersRunning(true);
        alert('✅ Workers started successfully!');
      } else {
        alert('Failed to start workers: ' + data.message);
      }
    } catch (error) {
      alert('Error starting workers: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const stopWorkforce = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBase}/agentic/stop-workforce`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const data = await response.json();
      if (data.success) {
        setWorkersRunning(false);
        alert('⏹️ Workers stopped successfully!');
      } else {
        alert('Failed to stop workers: ' + data.message);
      }
    } catch (error) {
      alert('Error stopping workers: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const startAutoWorkflow = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBase}/agentic/auto-workflow`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domains: topicDomains,
          topics_per_domain: topicsPerDomain,
          num_workers: 1
        })
      });
      
      const data = await response.json();
      if (data.success) {
        alert(`🚀 Automated workflow started! Generated ${data.workflow_results.stage_2_jobs.total_jobs} jobs.`);
        loadInitialData();
      } else {
        alert('Failed to start workflow: ' + data.message);
      }
    } catch (error) {
      alert('Error starting workflow: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const generateTopicsForReview = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBase}/agentic/review-generated-topics?domains=${topicDomains.join(',')}&topics_per_domain=${topicsPerDomain}`);
      const data = await response.json();
      
      if (data.success) {
        setReviewTopics(data.topics_for_review);
        setShowTopicReview(true);
      } else {
        alert('Failed to generate topics: ' + data.message);
      }
    } catch (error) {
      alert('Error generating topics: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const approveSelectedTopics = async () => {
    const selectedTopics = reviewTopics.filter(topic => topic.selected);
    
    if (selectedTopics.length === 0) {
      alert('Please select at least one topic');
      return;
    }
    
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBase}/agentic/approve-reviewed-topics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selected_topics: selectedTopics })
      });
      
      const data = await response.json();
      if (data.success) {
        alert(`✅ Approved ${selectedTopics.length} topics and added to job queue!`);
        setShowTopicReview(false);
        loadInitialData();
      } else {
        alert('Failed to approve topics: ' + data.message);
      }
    } catch (error) {
      alert('Error approving topics: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const uploadNextVideoToCloudflare = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBase}/upload/next-video-to-cloudflare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const data = await response.json();
      if (data.success) {
        alert(`📤 Video uploaded to Cloudflare!\n\nTopic: ${data.topic}\nLocal file deleted: ${data.local_file_deleted ? 'Yes' : 'No'}`);
        loadInitialData();
      } else {
        alert('Upload failed: ' + data.message);
      }
    } catch (error) {
      alert('Error uploading to Cloudflare: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const uploadVideoToPlatform = async (jobId = null) => {
    if (!oauthKey.trim()) {
      alert('Please enter your OAuth access key');
      return;
    }
    
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBase}/upload/youtube-from-cloudflare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: oauthKey,
          job_id: jobId,
          platform: uploadPlatform,
          privacy_status: 'private'
        })
      });
      
      const data = await response.json();
      if (data.success) {
        alert(`🎉 Video uploaded to ${uploadPlatform.toUpperCase()}!\n\nTopic: ${data.topic}\nVideo ID: ${data.video_id}\nOptimizations applied: ${data.optimization_applied.platform_specific ? 'Yes' : 'No'}`);
        loadInitialData();
      } else {
        alert('Upload failed: ' + data.message);
      }
    } catch (error) {
      alert(`Error uploading to ${uploadPlatform}: ` + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const completeUploadSequence = async () => {
    if (!oauthKey.trim()) {
      alert('Please enter your OAuth access key');
      return;
    }
    
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBase}/workflow/complete-upload-sequence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: oauthKey,
          privacy_status: 'private'
        })
      });
      
      const data = await response.json();
      if (data.success) {
        alert(`🎯 Complete upload sequence successful!\n\n📁 Cloudflare: ${data.cloudflare_url}\n📺 YouTube: ${data.youtube_url}\n🗑️ Local file deleted: ${data.local_file_deleted ? 'Yes' : 'No'}`);
        loadInitialData();
      } else {
        alert('Upload sequence failed: ' + data.message);
      }
    } catch (error) {
      alert('Error in upload sequence: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const cleanupCloudflareStorage = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiBase}/cloudflare/cleanup-storage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const data = await response.json();
      alert(`🧹 Cleanup completed!\n\nDeleted: ${data.deleted_videos?.length || 0} videos\nFreed space: ${data.total_freed_space_mb || 0} MB`);
      loadInitialData();
    } catch (error) {
      alert('Error cleaning up storage: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const toggleTopicSelection = (index) => {
    setReviewTopics(prev => 
      prev.map((topic, i) => 
        i === index ? { ...topic, selected: !topic.selected } : topic
      )
    );
  };
  
  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  const formatDuration = (seconds) => {
    if (!seconds) return '0s';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) return `${hours}h ${minutes}m ${secs}s`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="glass rounded-2xl p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">🤖 Agentic Video System</h2>
          
          <div className="flex items-center space-x-4">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              workersRunning 
                ? 'bg-green-900/20 text-green-400 border border-green-500/30'
                : 'bg-red-900/20 text-red-400 border border-red-500/30'
            }`}>
              {workersRunning ? '🟢 Workers Running' : '🔴 Workers Stopped'}
            </div>
            
            {workersRunning ? (
              <button
                onClick={stopWorkforce}
                disabled={isLoading}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                ⏹️ Stop Workers
              </button>
            ) : (
              <button
                onClick={startWorkforce}
                disabled={isLoading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                ▶️ Start Workers
              </button>
            )}
          </div>
        </div>
        
        {/* System Health Overview */}
        {systemStatus && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
              <div className="text-2xl font-bold text-blue-400">{systemStatus.health?.jobs_in_queue || 0}</div>
              <div className="text-sm text-gray-400">Jobs Queued</div>
            </div>
            
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
              <div className="text-2xl font-bold text-orange-400">{systemStatus.health?.jobs_processing || 0}</div>
              <div className="text-sm text-gray-400">Processing</div>
            </div>
            
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
              <div className="text-2xl font-bold text-green-400">{systemStatus.health?.videos_ready || 0}</div>
              <div className="text-sm text-gray-400">Videos Ready</div>
            </div>
            
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
              <div className="text-2xl font-bold text-purple-400">{cloudflareStatus?.storage_status?.current_videos || 0}/30</div>
              <div className="text-sm text-gray-400">Cloudflare Storage</div>
            </div>
          </div>
        )}
        
        {/* Quick Actions */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={startAutoWorkflow}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            🚀 Start Auto Workflow
          </button>
          
          <button
            onClick={generateTopicsForReview}
            disabled={isLoading}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            📝 Review Topics
          </button>
          
          <button
            onClick={uploadNextVideoToCloudflare}
            disabled={isLoading}
            className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:opacity-50"
          >
            📤 Upload to Cloudflare
          </button>
          
          <button
            onClick={completeUploadSequence}
            disabled={isLoading || !oauthKey.trim()}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            🎯 Complete Upload Sequence
          </button>
        </div>
      </div>
      
      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg">
        {['overview', 'queue', 'cloudflare', 'upload', 'activity'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-4 py-2 rounded-md font-medium transition-all capitalize ${
              activeTab === tab
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:text-white hover:bg-gray-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>
      
      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Metrics */}
          {metrics && (
            <div className="glass rounded-2xl p-6">
              <h3 className="text-xl font-semibold text-white mb-4">📊 Performance Metrics</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-300">Videos Generated:</span>
                  <span className="text-white font-medium">{metrics.performance?.total_videos_generated || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Success Rate:</span>
                  <span className="text-white font-medium">
                    {(metrics.performance?.success_rate * 100 || 0).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Avg Generation Time:</span>
                  <span className="text-white font-medium">
                    {formatDuration(metrics.performance?.average_generation_time)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Storage Used:</span>
                  <span className="text-white font-medium">
                    {formatBytes(metrics.storage?.total_storage_used)}
                  </span>
                </div>
              </div>
            </div>
          )}
          
          {/* Recent Activity */}
          {activityStream && (
            <div className="glass rounded-2xl p-6">
              <h3 className="text-xl font-semibold text-white mb-4">⚡ Recent Activity</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {activityStream.latest_completed?.slice(0, 5).map((job, index) => (
                  <div key={index} className="flex items-center space-x-3 p-2 bg-gray-800/30 rounded-lg">
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                    <div className="flex-1">
                      <div className="text-sm text-white">{job.topic}</div>
                      <div className="text-xs text-gray-400">{job.domain} • {job.progress}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {activeTab === 'queue' && queueStatus && (
        <div className="glass rounded-2xl p-6">
          <h3 className="text-xl font-semibold text-white mb-6">📋 Job Queue Status</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {Object.entries(queueStatus.by_status || {}).map(([status, count]) => (
              <div key={status} className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
                <div className="text-2xl font-bold text-blue-400">{count}</div>
                <div className="text-sm text-gray-400 capitalize">{status}</div>
              </div>
            ))}
          </div>
          
          {queueStatus.processing_jobs?.length > 0 && (
            <div className="mb-6">
              <h4 className="text-lg font-semibold text-white mb-3">🔄 Currently Processing</h4>
              <div className="space-y-4">
                {queueStatus.processing_jobs.map((job, index) => (
                  <div key={index} className="p-4 glass rounded-lg">
                    <div className="flex justify-between items-center mb-3">
                      <div>
                        <h5 className="text-white font-medium">{job.topic}</h5>
                        <div className="text-sm text-gray-400">{job.domain}</div>
                      </div>
                      <div className="text-orange-400 font-semibold">{job.progress}%</div>
                    </div>
                    
                    {job.job_id && (
                      <ProgressBar 
                        jobId={job.job_id}
                        autoStart={true}
                        showDetails={false}
                        onComplete={() => {
                          setTimeout(() => {
                            loadInitialData();
                          }, 1000);
                        }}
                      />
                    )}
                    
                    <div className="mt-2 text-xs text-gray-500">{job.message}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {queueStatus.next_jobs?.length > 0 && (
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">⏳ Next in Queue</h4>
              <div className="space-y-2">
                {queueStatus.next_jobs.map((job, index) => (
                  <div key={index} className="p-3 bg-gray-800/30 rounded-lg">
                    <div className="text-white">{job.topic}</div>
                    <div className="text-sm text-gray-400">{job.domain}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {activeTab === 'cloudflare' && cloudflareStatus && (
        <div className="space-y-6">
          <div className="glass rounded-2xl p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-white">☁️ Cloudflare Storage</h3>
              <button
                onClick={cleanupCloudflareStorage}
                disabled={isLoading}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                🧹 Cleanup Storage
              </button>
            </div>
            
            <div className="mb-6">
              <div className="flex justify-between mb-2">
                <span className="text-gray-300">Storage Used:</span>
                <span className="text-white">
                  {cloudflareStatus.storage_status?.current_videos || 0} / 30 videos
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div 
                  className="bg-blue-600 h-3 rounded-full transition-all"
                  style={{ 
                    width: `${((cloudflareStatus.storage_status?.current_videos || 0) / 30) * 100}%` 
                  }}
                ></div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  {cloudflareStatus.storage_status?.available_slots || 0}
                </div>
                <div className="text-sm text-gray-400">Available Slots</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">
                  {cloudflareStatus.storage_stats?.total_size_mb || 0} MB
                </div>
                <div className="text-sm text-gray-400">Total Size</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">
                  {cloudflareStatus.storage_stats?.recent_uploads_7_days || 0}
                </div>
                <div className="text-sm text-gray-400">Recent Uploads</div>
              </div>
            </div>
            
            {cloudflareStatus.storage_status?.storage_full && (
              <div className="mt-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                <div className="text-red-400 font-medium">⚠️ Storage Full</div>
                <div className="text-sm text-red-300">
                  Please delete some videos or cleanup will happen automatically
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {activeTab === 'upload' && (
        <div className="space-y-6">
          <div className="glass rounded-2xl p-6">
            <h3 className="text-xl font-semibold text-white mb-6">📺 Upload Management</h3>
            
            {/* OAuth Key Input */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                OAuth Access Key
              </label>
              <input
                type="password"
                value={oauthKey}
                onChange={(e) => setOauthKey(e.target.value)}
                placeholder="Enter your OAuth access key..."
                className="w-full p-3 input-dark rounded-lg"
              />
            </div>
            
            {/* Platform Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Upload Platform
              </label>
              <select
                value={uploadPlatform}
                onChange={(e) => setUploadPlatform(e.target.value)}
                className="w-full p-3 input-dark rounded-lg"
              >
                <option value="youtube">YouTube</option>
                <option value="instagram">Instagram</option>
                <option value="tiktok">TikTok</option>
              </select>
            </div>
            
            {/* Upload Actions */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => uploadVideoToPlatform()}
                disabled={isLoading || !oauthKey.trim()}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                📺 Upload Next Video
              </button>
              
              <button
                onClick={completeUploadSequence}
                disabled={isLoading || !oauthKey.trim()}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                🎯 Complete Sequence
              </button>
            </div>
          </div>
          
          {/* Completed Videos */}
          {completedVideos.length > 0 && (
            <div className="glass rounded-2xl p-6">
              <h4 className="text-lg font-semibold text-white mb-4">✅ Ready for Upload</h4>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {completedVideos.slice(0, 5).map((video, index) => (
                  <div key={index} className="flex justify-between items-center p-3 bg-gray-800/30 rounded-lg">
                    <div>
                      <div className="text-white font-medium">{video.topic}</div>
                      <div className="text-sm text-gray-400">{video.domain} • {video.completed_at}</div>
                    </div>
                    <button
                      onClick={() => uploadVideoToPlatform(video.job_id)}
                      disabled={isLoading || !oauthKey.trim()}
                      className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                    >
                      Upload
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {activeTab === 'activity' && activityStream && (
        <div className="glass rounded-2xl p-6">
          <h3 className="text-xl font-semibold text-white mb-6">📈 Activity Stream</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
              <div className="text-2xl font-bold text-blue-400">{activityStream.summary?.total_jobs || 0}</div>
              <div className="text-sm text-gray-400">Total Jobs</div>
            </div>
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
              <div className="text-2xl font-bold text-green-400">{activityStream.summary?.recently_completed || 0}</div>
              <div className="text-sm text-gray-400">Recently Completed</div>
            </div>
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
              <div className="text-2xl font-bold text-orange-400">{activityStream.summary?.currently_processing || 0}</div>
              <div className="text-sm text-gray-400">Processing</div>
            </div>
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
              <div className="text-2xl font-bold text-red-400">{activityStream.summary?.failed || 0}</div>
              <div className="text-sm text-gray-400">Failed</div>
            </div>
          </div>
          
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {activityStream.recent_jobs?.map((job, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-gray-800/30 rounded-lg">
                <div className={`w-3 h-3 rounded-full ${
                  job.status === 'completed' ? 'bg-green-400' :
                  job.status === 'processing' ? 'bg-orange-400' :
                  job.status === 'failed' ? 'bg-red-400' : 'bg-gray-400'
                }`}></div>
                <div className="flex-1">
                  <div className="text-white">{job.topic}</div>
                  <div className="text-sm text-gray-400">
                    {job.domain} • {job.status} • {job.progress}%
                  </div>
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(job.created_at).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Topic Review Modal */}
      {showTopicReview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto border border-gray-600">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-white">📝 Review Generated Topics</h3>
              <button
                onClick={() => setShowTopicReview(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="mb-4">
              <div className="text-sm text-gray-400 mb-2">
                Selected: {reviewTopics.filter(t => t.selected).length} / {reviewTopics.length}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setReviewTopics(prev => prev.map(t => ({...t, selected: true})))}
                  className="px-3 py-1 bg-green-600 text-white text-sm rounded"
                >
                  Select All
                </button>
                <button
                  onClick={() => setReviewTopics(prev => prev.map(t => ({...t, selected: false})))}
                  className="px-3 py-1 bg-red-600 text-white text-sm rounded"
                >
                  Deselect All
                </button>
              </div>
            </div>
            
            <div className="space-y-3 mb-6 max-h-96 overflow-y-auto">
              {reviewTopics.map((topic, index) => (
                <div 
                  key={index} 
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    topic.selected 
                      ? 'bg-blue-900/20 border-blue-500/30' 
                      : 'bg-gray-800/50 border-gray-600 hover:border-gray-500'
                  }`}
                  onClick={() => toggleTopicSelection(index)}
                >
                  <div className="flex items-start space-x-3">
                    <div className={`w-4 h-4 rounded border-2 mt-1 flex items-center justify-center ${
                      topic.selected ? 'bg-blue-600 border-blue-600' : 'border-gray-500'
                    }`}>
                      {topic.selected && <span className="text-white text-xs">✓</span>}
                    </div>
                    <div className="flex-1">
                      <div className="text-white font-medium">{topic.topic}</div>
                      <div className="text-sm text-gray-400 mb-1">{topic.domain}</div>
                      <div className="text-xs text-gray-500">
                        Keywords: {topic.keywords?.join(', ')}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowTopicReview(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={approveSelectedTopics}
                disabled={isLoading || reviewTopics.filter(t => t.selected).length === 0}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {isLoading ? 'Processing...' : `Approve ${reviewTopics.filter(t => t.selected).length} Topics`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}