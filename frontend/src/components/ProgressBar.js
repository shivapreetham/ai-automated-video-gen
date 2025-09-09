'use client';

import { useState, useEffect } from 'react';

export default function ProgressBar({ 
  jobId, 
  onComplete, 
  onError,
  autoStart = true,
  showDetails = true 
}) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('pending');
  const [message, setMessage] = useState('');
  const [stages, setStages] = useState([]);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (autoStart && jobId) {
      startPolling();
    }
    
    return () => {
      stopPolling();
    };
  }, [jobId]);

  const startPolling = () => {
    if (!jobId || isPolling) return;
    
    setIsPolling(true);
    pollProgress();
  };

  const stopPolling = () => {
    setIsPolling(false);
  };

  const pollProgress = async () => {
    if (!isPolling) return;

    try {
      const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/jobs/${jobId}/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      setProgress(data.progress || 0);
      setStatus(data.status || 'pending');
      setMessage(data.message || '');
      
      // Create stage breakdown based on progress
      const newStages = [
        { 
          name: 'Script Generation', 
          progress: data.progress >= 20 ? 100 : (data.progress / 20) * 100,
          status: data.progress >= 20 ? 'completed' : data.progress > 0 ? 'active' : 'pending'
        },
        { 
          name: 'Audio Generation', 
          progress: data.progress >= 40 ? 100 : data.progress > 20 ? ((data.progress - 20) / 20) * 100 : 0,
          status: data.progress >= 40 ? 'completed' : data.progress > 20 ? 'active' : 'pending'
        },
        { 
          name: 'Image Generation', 
          progress: data.progress >= 60 ? 100 : data.progress > 40 ? ((data.progress - 40) / 20) * 100 : 0,
          status: data.progress >= 60 ? 'completed' : data.progress > 40 ? 'active' : 'pending'
        },
        { 
          name: 'Video Assembly', 
          progress: data.progress >= 80 ? 100 : data.progress > 60 ? ((data.progress - 60) / 20) * 100 : 0,
          status: data.progress >= 80 ? 'completed' : data.progress > 60 ? 'active' : 'pending'
        },
        { 
          name: 'Final Processing', 
          progress: data.progress >= 100 ? 100 : data.progress > 80 ? ((data.progress - 80) / 20) * 100 : 0,
          status: data.progress >= 100 ? 'completed' : data.progress > 80 ? 'active' : 'pending'
        }
      ];
      
      setStages(newStages);

      if (data.status === 'completed') {
        setIsPolling(false);
        if (onComplete) onComplete(data);
      } else if (data.status === 'failed') {
        setIsPolling(false);
        setError(data.error || 'Job failed');
        if (onError) onError(data.error || 'Job failed');
      } else {
        // Continue polling
        setTimeout(() => {
          if (isPolling) {
            pollProgress();
          }
        }, 2000);
      }
    } catch (error) {
      console.error('Error polling progress:', error);
      setError(error.message);
      setIsPolling(false);
      if (onError) onError(error.message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-400';
      case 'failed':
        return 'text-red-400';
      case 'active':
      case 'processing':
        return 'text-blue-400';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusIcon = (stageStatus) => {
    switch (stageStatus) {
      case 'completed':
        return '✓';
      case 'active':
        return '⏳';
      default:
        return '○';
    }
  };

  if (!jobId) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* Main Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-300">
            Overall Progress
          </span>
          <span className={`text-sm font-semibold ${getStatusColor(status)}`}>
            {progress.toFixed(1)}%
          </span>
        </div>
        
        <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
          <div 
            className="progress-bar h-full rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        <div className={`text-xs text-center ${getStatusColor(status)}`}>
          {message || status.charAt(0).toUpperCase() + status.slice(1)}
        </div>
      </div>

      {/* Stage Breakdown */}
      {showDetails && stages.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-300">Progress Details</h4>
          
          <div className="grid grid-cols-1 gap-2">
            {stages.map((stage, index) => (
              <div 
                key={index}
                className="flex items-center space-x-3 p-2 bg-gray-800/30 rounded-lg"
              >
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                  stage.status === 'completed' 
                    ? 'bg-green-600 text-white' 
                    : stage.status === 'active'
                    ? 'bg-blue-600 text-white animate-pulse'
                    : 'bg-gray-600 text-gray-300'
                }`}>
                  {getStatusIcon(stage.status)}
                </div>
                
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs font-medium text-gray-300">
                      {stage.name}
                    </span>
                    <span className="text-xs text-gray-400">
                      {stage.progress.toFixed(0)}%
                    </span>
                  </div>
                  
                  <div className="w-full bg-gray-700 rounded-full h-1">
                    <div 
                      className={`h-1 rounded-full transition-all duration-300 ${
                        stage.status === 'completed' 
                          ? 'bg-green-500' 
                          : stage.status === 'active'
                          ? 'bg-blue-500'
                          : 'bg-gray-600'
                      }`}
                      style={{ width: `${stage.progress}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
          <div className="flex items-center space-x-2">
            <span className="text-red-400 font-medium">Error:</span>
            <span className="text-red-300 text-sm">{error}</span>
          </div>
        </div>
      )}

      {/* Actions */}
      {status === 'completed' && (
        <div className="flex justify-center">
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-green-600/20 text-green-400 border border-green-500/30 rounded-lg">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-sm font-medium">Generation Complete!</span>
          </div>
        </div>
      )}
    </div>
  );
}