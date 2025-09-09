'use client';

import { useState, useEffect } from 'react';

export default function SettingsPage() {
  const [oauthCredentials, setOauthCredentials] = useState({
    youtube_client_id: '',
    youtube_client_secret: '',
    youtube_access_token: '',
    youtube_refresh_token: '',
  });

  const [systemSettings, setSystemSettings] = useState({
    auto_cleanup: true,
    max_concurrent_jobs: 3,
    default_video_quality: 'high',
    storage_limit_gb: 50,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [activeSection, setActiveSection] = useState('oauth');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      
      // Load OAuth credentials
      const oauthResponse = await fetch(`${apiBase}/oauth/credentials`);
      if (oauthResponse.ok) {
        const oauthData = await oauthResponse.json();
        setOauthCredentials(oauthData.credentials || {});
      }

      // Load system settings
      const settingsResponse = await fetch(`${apiBase}/system/settings`);
      if (settingsResponse.ok) {
        const settingsData = await settingsResponse.json();
        setSystemSettings(settingsData.settings || {});
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveOauthCredentials = async () => {
    setIsLoading(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/oauth/update-credentials`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credentials: oauthCredentials })
      });

      if (response.ok) {
        alert('✅ OAuth credentials saved successfully!');
      } else {
        throw new Error('Failed to save credentials');
      }
    } catch (error) {
      console.error('Error saving OAuth credentials:', error);
      alert('❌ Failed to save OAuth credentials');
    } finally {
      setIsLoading(false);
    }
  };

  const saveSystemSettings = async () => {
    setIsLoading(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/system/update-settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings: systemSettings })
      });

      if (response.ok) {
        alert('✅ System settings saved successfully!');
      } else {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving system settings:', error);
      alert('❌ Failed to save system settings');
    } finally {
      setIsLoading(false);
    }
  };

  const testOauthConnection = async () => {
    setIsLoading(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/oauth/test-connection`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credentials: oauthCredentials })
      });

      const result = await response.json();
      if (result.success) {
        alert('✅ OAuth connection test successful!');
      } else {
        alert(`❌ OAuth connection failed: ${result.error}`);
      }
    } catch (error) {
      console.error('Error testing OAuth connection:', error);
      alert('❌ Failed to test OAuth connection');
    } finally {
      setIsLoading(false);
    }
  };

  const clearStorageData = async () => {
    if (!confirm('This will delete all local video files and clear the cache. Continue?')) {
      return;
    }

    setIsLoading(true);
    try {
      const apiBase = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/system/clear-storage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const result = await response.json();
      if (result.success) {
        alert(`✅ Storage cleared successfully! Freed ${result.freed_space_mb} MB`);
      } else {
        alert(`❌ Failed to clear storage: ${result.error}`);
      }
    } catch (error) {
      console.error('Error clearing storage:', error);
      alert('❌ Failed to clear storage');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">Settings</h2>
        <p className="text-gray-400 mt-1">Manage your application settings and OAuth credentials</p>
      </div>

      {/* Section Navigation */}
      <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg">
        <button
          onClick={() => setActiveSection('oauth')}
          className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
            activeSection === 'oauth'
              ? 'bg-blue-600 text-white'
              : 'text-gray-300 hover:text-white hover:bg-gray-700'
          }`}
        >
          🔐 OAuth Credentials
        </button>
        <button
          onClick={() => setActiveSection('system')}
          className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
            activeSection === 'system'
              ? 'bg-blue-600 text-white'
              : 'text-gray-300 hover:text-white hover:bg-gray-700'
          }`}
        >
          ⚙️ System Settings
        </button>
        <button
          onClick={() => setActiveSection('maintenance')}
          className={`flex-1 px-4 py-2 rounded-md font-medium transition-all ${
            activeSection === 'maintenance'
              ? 'bg-blue-600 text-white'
              : 'text-gray-300 hover:text-white hover:bg-gray-700'
          }`}
        >
          🔧 Maintenance
        </button>
      </div>

      {/* OAuth Credentials Section */}
      {activeSection === 'oauth' && (
        <div className="glass rounded-2xl p-6 space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-semibold text-white">YouTube OAuth Credentials</h3>
            <div className="flex space-x-3">
              <button
                onClick={testOauthConnection}
                disabled={isLoading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Test Connection
              </button>
              <button
                onClick={saveOauthCredentials}
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Save Credentials
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Client ID *
              </label>
              <input
                type="text"
                value={oauthCredentials.youtube_client_id}
                onChange={(e) => setOauthCredentials(prev => ({
                  ...prev,
                  youtube_client_id: e.target.value
                }))}
                placeholder="Enter YouTube Client ID"
                className="w-full p-3 input-dark rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Client Secret *
              </label>
              <input
                type="password"
                value={oauthCredentials.youtube_client_secret}
                onChange={(e) => setOauthCredentials(prev => ({
                  ...prev,
                  youtube_client_secret: e.target.value
                }))}
                placeholder="Enter YouTube Client Secret"
                className="w-full p-3 input-dark rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Access Token
              </label>
              <input
                type="password"
                value={oauthCredentials.youtube_access_token}
                onChange={(e) => setOauthCredentials(prev => ({
                  ...prev,
                  youtube_access_token: e.target.value
                }))}
                placeholder="Enter Access Token"
                className="w-full p-3 input-dark rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Refresh Token
              </label>
              <input
                type="password"
                value={oauthCredentials.youtube_refresh_token}
                onChange={(e) => setOauthCredentials(prev => ({
                  ...prev,
                  youtube_refresh_token: e.target.value
                }))}
                placeholder="Enter Refresh Token"
                className="w-full p-3 input-dark rounded-lg"
              />
            </div>
          </div>

          <div className="bg-blue-900/20 border border-blue-500/20 rounded-lg p-4">
            <h4 className="font-medium text-blue-400 mb-2">Setup Instructions:</h4>
            <ol className="text-sm text-blue-300 space-y-1 list-decimal list-inside">
              <li>Go to <a href="https://console.developers.google.com/" target="_blank" rel="noopener noreferrer" className="underline">Google Developers Console</a></li>
              <li>Create a new project or select existing one</li>
              <li>Enable YouTube Data API v3</li>
              <li>Create OAuth 2.0 credentials</li>
              <li>Copy the Client ID and Client Secret here</li>
              <li>Use OAuth Playground to get Access/Refresh tokens</li>
            </ol>
          </div>
        </div>
      )}

      {/* System Settings Section */}
      {activeSection === 'system' && (
        <div className="glass rounded-2xl p-6 space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-semibold text-white">System Settings</h3>
            <button
              onClick={saveSystemSettings}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Save Settings
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Max Concurrent Jobs
              </label>
              <select
                value={systemSettings.max_concurrent_jobs}
                onChange={(e) => setSystemSettings(prev => ({
                  ...prev,
                  max_concurrent_jobs: parseInt(e.target.value)
                }))}
                className="w-full p-3 input-dark rounded-lg"
              >
                <option value={1}>1 Job</option>
                <option value={2}>2 Jobs</option>
                <option value={3}>3 Jobs</option>
                <option value={4}>4 Jobs</option>
                <option value={5}>5 Jobs</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Default Video Quality
              </label>
              <select
                value={systemSettings.default_video_quality}
                onChange={(e) => setSystemSettings(prev => ({
                  ...prev,
                  default_video_quality: e.target.value
                }))}
                className="w-full p-3 input-dark rounded-lg"
              >
                <option value="low">Low (720p)</option>
                <option value="medium">Medium (1080p)</option>
                <option value="high">High (1440p)</option>
                <option value="ultra">Ultra (4K)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Storage Limit (GB)
              </label>
              <input
                type="number"
                value={systemSettings.storage_limit_gb}
                onChange={(e) => setSystemSettings(prev => ({
                  ...prev,
                  storage_limit_gb: parseInt(e.target.value)
                }))}
                min="10"
                max="500"
                className="w-full p-3 input-dark rounded-lg"
              />
            </div>

            <div className="flex items-center">
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={systemSettings.auto_cleanup}
                  onChange={(e) => setSystemSettings(prev => ({
                    ...prev,
                    auto_cleanup: e.target.checked
                  }))}
                  className="rounded"
                />
                <div>
                  <span className="text-gray-300 font-medium">Auto Cleanup</span>
                  <div className="text-sm text-gray-400">
                    Automatically delete old videos when storage limit is reached
                  </div>
                </div>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Maintenance Section */}
      {activeSection === 'maintenance' && (
        <div className="space-y-6">
          <div className="glass rounded-2xl p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Storage Management</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-gray-800/50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-400">2.4 GB</div>
                <div className="text-sm text-gray-400">Local Storage Used</div>
              </div>
              <div className="bg-gray-800/50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-400">15</div>
                <div className="text-sm text-gray-400">Videos in Cloud</div>
              </div>
              <div className="bg-gray-800/50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-orange-400">8</div>
                <div className="text-sm text-gray-400">Local Videos</div>
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={clearStorageData}
                disabled={isLoading}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                Clear Local Storage
              </button>
              <button
                disabled={isLoading}
                className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50"
              >
                Optimize Database
              </button>
              <button
                disabled={isLoading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Export Logs
              </button>
            </div>
          </div>

          <div className="glass rounded-2xl p-6">
            <h3 className="text-xl font-semibold text-white mb-4">System Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
              <div>
                <h4 className="font-medium text-gray-300 mb-2">Application</h4>
                <div className="space-y-1 text-gray-400">
                  <div>Version: 2.1.0</div>
                  <div>Build: 20231215-1430</div>
                  <div>Environment: Production</div>
                </div>
              </div>
              <div>
                <h4 className="font-medium text-gray-300 mb-2">System</h4>
                <div className="space-y-1 text-gray-400">
                  <div>Platform: {navigator.platform}</div>
                  <div>Browser: {navigator.userAgent.split(' ')[0]}</div>
                  <div>Memory: ~{Math.round(performance.memory?.usedJSHeapSize / 1024 / 1024) || 'N/A'} MB</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading Overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 flex items-center space-x-3">
            <div className="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-white">Processing...</span>
          </div>
        </div>
      )}
    </div>
  );
}