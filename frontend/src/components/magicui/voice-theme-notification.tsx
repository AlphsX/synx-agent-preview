'use client';

import { useEffect } from 'react';

interface VoiceThemeNotificationProps {
  message: string;
  theme: 'dark' | 'light';
  isVisible: boolean;
  onClose: () => void;
  type?: 'info' | 'success' | 'error' | 'warning'; // Add type property
}

export function VoiceThemeNotification({ 
  message, 
  theme, 
  isVisible, 
  onClose,
  type = 'info' // Default to info
}: VoiceThemeNotificationProps) {
  // Auto-dismiss after 3 seconds
  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => {
        onClose();
      }, type === 'error' ? 5000 : 3000); // Show errors for longer
      
      return () => clearTimeout(timer);
    }
  }, [isVisible, onClose, type]);

  if (!isVisible) return null;

  // Determine if this is a sidebar notification based on the message
  const isSidebarNotification = message.includes('Sidebar');
  
  // Select appropriate icon based on notification type
  const renderIcon = () => {
    // Sidebar notifications now use contextually appropriate icons
    if (isSidebarNotification) {
      switch (type) {
        case 'success':
          // Sidebar success icon (checkmark with sidebar representation)
          return (
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" 
              fill="currentColor"
              className="w-full h-full animate-luxury-glow"
            >
              <path d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm0 5a1 1 0 011-1h14a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1v-7zm2 2a1 1 0 000 2h2a1 1 0 000-2H6zm0 4a1 1 0 000 2h2a1 1 0 000-2H6zm4-4a1 1 0 000 2h6a1 1 0 000-2h-6zm0 4a1 1 0 000 2h6a1 1 0 000-2h-6z" />
              <path d="M19 5h2v14h-2a1 1 0 01-1-1V6a1 1 0 011-1z" />
              <path 
                fillRule="evenodd" 
                d="M9.5 14.5a.75.75 0 001.06 0l3.5-3.5a.75.75 0 00-1.06-1.06l-2.22 2.22L9.5 10.5a.75.75 0 00-1.06 1.06l1.72 1.72z" 
                clipRule="evenodd" 
              />
            </svg>
          );
        case 'error':
          // Sidebar error icon (sidebar with error indicator)
          return (
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" 
              fill="currentColor"
              className="w-full h-full animate-luxury-glow"
            >
              <path d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm0 5a1 1 0 011-1h14a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1v-7zm2 2a1 1 0 000 2h2a1 1 0 000-2H6zm0 4a1 1 0 000 2h2a1 1 0 000-2H6zm4-4a1 1 0 000 2h6a1 1 0 000-2h-6zm0 4a1 1 0 000 2h6a1 1 0 000-2h-6z" />
              <path d="M19 5h2v14h-2a1 1 0 01-1-1V6a1 1 0 011-1z" />
              <circle cx="16.5" cy="9.5" r="1.5" fill="currentColor" />
              <path d="M15 12l3-3m0 3l-3-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          );
        case 'warning':
          // Sidebar warning icon (sidebar with warning triangle)
          return (
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" 
              fill="currentColor"
              className="w-full h-full animate-luxury-glow"
            >
              <path d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm0 5a1 1 0 011-1h14a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1v-7zm2 2a1 1 0 000 2h2a1 1 0 000-2H6zm0 4a1 1 0 000 2h2a1 1 0 000-2H6zm4-4a1 1 0 000 2h6a1 1 0 000-2h-6zm0 4a1 1 0 000 2h6a1 1 0 000-2h-6z" />
              <path d="M19 5h2v14h-2a1 1 0 01-1-1V6a1 1 0 011-1z" />
              <path 
                fillRule="evenodd" 
                d="M12 7.5a.75.75 0 01.75.75v5a.75.75 0 01-1.5 0V8.25A.75.75 0 0112 7.5zm0 9a.75.75 0 100-1.5.75.75 0 000 1.5z" 
                clipRule="evenodd" 
              />
            </svg>
          );
        case 'info':
        default:
          // Sidebar info icon (sidebar with info circle)
          return (
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" 
              fill="currentColor"
              className="w-full h-full animate-luxury-glow"
            >
              <path d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm0 5a1 1 0 011-1h14a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1v-7zm2 2a1 1 0 000 2h2a1 1 0 000-2H6zm0 4a1 1 0 000 2h2a1 1 0 000-2H6zm4-4a1 1 0 000 2h6a1 1 0 000-2h-6zm0 4a1 1 0 000 2h6a1 1 0 000-2h-6z" />
              <path d="M19 5h2v14h-2a1 1 0 01-1-1V6a1 1 0 011-1z" />
              <path 
                fillRule="evenodd" 
                d="M12 9.5a.75.75 0 01.75.75v.75a.75.75 0 01-1.5 0v-.75A.75.75 0 0112 9.5zm-.75 3a.75.75 0 000 1.5h1.5a.75.75 0 000-1.5h-1.5z" 
                clipRule="evenodd" 
              />
              <circle cx="12" cy="12" r="7.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          );
      }
    }
    
    // Different icons for different notification types
    switch (type) {
      case 'success':
        // Checkmark icon for success
        return (
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            viewBox="0 0 24 24" 
            fill="currentColor"
            className="w-full h-full animate-luxury-glow"
          >
            <path 
              fillRule="evenodd" 
              d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" 
              clipRule="evenodd" 
            />
          </svg>
        );
      case 'error':
        // Error icon (exclamation circle)
        return (
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            viewBox="0 0 24 24" 
            fill="currentColor"
            className="w-full h-full animate-luxury-glow"
          >
            <path 
              fillRule="evenodd" 
              d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zM12 8.25a.75.75 0 01.75.75v3.75a.75.75 0 01-1.5 0V9a.75.75 0 01.75-.75zm0 8.25a.75.75 0 100-1.5.75.75 0 000 1.5z" 
              clipRule="evenodd" 
            />
          </svg>
        );
      case 'warning':
        // Warning icon (exclamation triangle)
        return (
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            viewBox="0 0 24 24" 
            fill="currentColor"
            className="w-full h-full animate-luxury-glow"
          >
            <path 
              fillRule="evenodd" 
              d="M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003zM12 8.25a.75.75 0 01.75.75v3.75a.75.75 0 01-1.5 0V9a.75.75 0 01.75-.75zm0 8.25a.75.75 0 100-1.5.75.75 0 000 1.5z" 
              clipRule="evenodd" 
            />
          </svg>
        );
      case 'info':
      default:
        // Info icon (i in circle) or theme-specific icons
        if (theme === 'dark') {
          // Moon icon for dark mode
          return (
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" 
              fill="currentColor"
              className="w-full h-full animate-luxury-glow"
            >
              <path 
                fillRule="evenodd" 
                d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z" 
                clipRule="evenodd" 
              />
            </svg>
          );
        } else {
          // Sun icon for light mode
          return (
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" 
              fill="currentColor"
              className="w-full h-full animate-luxury-glow"
            >
              <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z" />
            </svg>
          );
        }
    }
  };

  // Determine styling based on notification type
  const getNotificationStyle = () => {
    // Apply contextually appropriate styling for sidebar notifications
    if (isSidebarNotification) {
      switch (type) {
        case 'success':
          return theme === 'dark'
            ? 'bg-gradient-to-r from-cyan-900/90 via-cyan-800/90 to-cyan-900/90 text-cyan-100 border-cyan-700/50'
            : 'bg-gradient-to-r from-blue-100/90 via-blue-50/90 to-blue-100/90 text-blue-900 border-blue-300/50';
        case 'error':
          return theme === 'dark'
            ? 'bg-gradient-to-r from-rose-900/90 via-rose-800/90 to-rose-900/90 text-rose-100 border-rose-700/50'
            : 'bg-gradient-to-r from-rose-100/90 via-rose-50/90 to-rose-100/90 text-rose-900 border-rose-300/50';
        case 'warning':
          return theme === 'dark'
            ? 'bg-gradient-to-r from-amber-900/90 via-amber-800/90 to-amber-900/90 text-amber-100 border-amber-700/50'
            : 'bg-gradient-to-r from-amber-100/90 via-amber-50/90 to-amber-100/90 text-amber-900 border-amber-300/50';
        case 'info':
        default:
          return theme === 'dark' 
            ? 'bg-gradient-to-r from-sky-900/90 via-sky-800/90 to-sky-900/90 text-sky-100 border-sky-700/50'
            : 'bg-gradient-to-r from-sky-100/90 via-sky-50/90 to-sky-100/90 text-sky-900 border-sky-300/50';
      }
    }
    
    // For regular notifications, use the gradient classes which already include appropriate shadows
    switch (type) {
      case 'success':
        return theme === 'dark'
          ? 'luxury-gradient-success-dark'
          : 'luxury-gradient-success-light';
      case 'error':
        return theme === 'dark'
          ? 'luxury-gradient-error-dark'
          : 'luxury-gradient-error-light';
      case 'warning':
        return theme === 'dark'
          ? 'luxury-gradient-warning-dark'
          : 'luxury-gradient-warning-light';
      case 'info':
      default:
        return theme === 'dark' 
          ? 'luxury-gradient-info-dark'
          : 'luxury-gradient-info-light';
    }
  };

  // Determine icon color based on notification type
  const getIconColor = () => {
    // Apply contextually appropriate icon colors for sidebar notifications
    if (isSidebarNotification) {
      switch (type) {
        case 'success':
          return theme === 'dark' ? 'text-cyan-400' : 'text-blue-500';
        case 'error':
          return theme === 'dark' ? 'text-rose-400' : 'text-rose-500';
        case 'warning':
          return theme === 'dark' ? 'text-amber-400' : 'text-amber-500';
        case 'info':
        default:
          return theme === 'dark' ? 'text-sky-300' : 'text-sky-500';
      }
    }
    
    switch (type) {
      case 'success':
        return theme === 'dark' ? 'text-emerald-400' : 'text-green-500';
      case 'error':
        return theme === 'dark' ? 'text-red-400' : 'text-red-500';
      case 'warning':
        return theme === 'dark' ? 'text-amber-400' : 'text-amber-500';
      case 'info':
      default:
        return theme === 'dark' ? 'text-purple-300' : 'text-amber-500';
    }
  };

  // Format message to support multi-line display
  const formatMessage = () => {
    // If message contains a period followed by a space, split it into two lines
    if (message.includes('. ')) {
      const parts = message.split('. ', 2);
      return (
        <>
          <div className="luxury-font-primary">{parts[0]}.</div>
          {parts[1] && <div className="mt-1 text-sm luxury-font-secondary">{parts[1]}</div>}
        </>
      );
    }
    // If message is still long, split at a natural break point
    else if (message.length > 50) {
      // Try to find a natural break point around the middle
      const breakPoint = Math.floor(message.length / 2);
      const spaceIndex = message.lastIndexOf(' ', breakPoint);
      if (spaceIndex > 0) {
        return (
          <>
            <div className="luxury-font-primary">{message.substring(0, spaceIndex)}</div>
            <div className="mt-1 text-sm luxury-font-secondary">{message.substring(spaceIndex + 1)}</div>
          </>
        );
      }
    }
    // Return message as is if no splitting is needed
    return <span className="luxury-font-primary">{message}</span>;
  };

  return (
    <div 
      className={`
        fixed top-4 left-1/2 transform -translate-x-1/2 z-50
        px-6 py-4 rounded-2xl backdrop-blur-md
        border transition-all duration-500
        animate-luxury-enter
        ${getNotificationStyle()}
        ${isSidebarNotification ? 'luxury-shadow-' + type : ''}
        flex items-start space-x-3
        ${isSidebarNotification ? 'min-w-[300px]' : 'max-w-md'}
      `}
      role="alert"
      aria-live="polite"
    >
      <div className={`flex-shrink-0 w-6 h-6 ${getIconColor()} luxury-icon-glow`}>
        {renderIcon()}
      </div>
      <div className={`${isSidebarNotification ? 'text-lg' : 'text-base'} luxury-text-glow`}>
        {formatMessage()}
      </div>
      <button 
        onClick={onClose}
        className="ml-2 text-sm opacity-70 hover:opacity-100 focus:outline-none transition-opacity duration-200 luxury-icon-glow"
        aria-label="Close notification"
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          className="h-5 w-5" 
          viewBox="0 0 20 20" 
          fill="currentColor"
        >
          <path 
            fillRule="evenodd" 
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" 
            clipRule="evenodd" 
          />
        </svg>
      </button>
    </div>
  );
}