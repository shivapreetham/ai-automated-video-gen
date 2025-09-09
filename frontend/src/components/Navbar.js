'use client';

import { useState } from 'react';

export default function Navbar({ activeTab, setActiveTab }) {
  return (
    <nav className="bg-gray-900/95 backdrop-blur-md border-b border-gray-700/50 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">AI</span>
              </div>
              <h1 className="ml-3 text-xl font-bold text-white">Video Generator</h1>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              <NavLink 
                active={activeTab === 'agent'} 
                onClick={() => setActiveTab('agent')}
                icon="🤖"
                text="Agent"
              />
              <NavLink 
                active={activeTab === 'custom'} 
                onClick={() => setActiveTab('custom')}
                icon="⚙️"
                text="Custom"
              />
              <NavLink 
                active={activeTab === 'data'} 
                onClick={() => setActiveTab('data')}
                icon="📊"
                text="Data"
              />
              <NavLink 
                active={activeTab === 'settings'} 
                onClick={() => setActiveTab('settings')}
                icon="🔧"
                text="Settings"
              />
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button className="text-gray-300 hover:text-white p-2 rounded-md">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

function NavLink({ active, onClick, icon, text }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center space-x-2 ${
        active
          ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
          : 'text-gray-300 hover:text-white hover:bg-gray-700/50'
      }`}
    >
      <span className="text-base">{icon}</span>
      <span>{text}</span>
    </button>
  );
}