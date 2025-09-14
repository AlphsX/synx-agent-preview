'use client';

import { useState, useEffect, useRef } from 'react';

export default function VoiceSidebarTest() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isDesktopSidebarCollapsed, setIsDesktopSidebarCollapsed] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [notification, setNotification] = useState<{ message: string; isVisible: boolean }>({ 
    message: '', 
    isVisible: false 
  });
  const speechRecognitionRef = useRef<any>(null);
  const isStartingRef = useRef(false);

  // Initialize SpeechRecognition API
  useEffect(() => {
    // Check if browser supports SpeechRecognition
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.error('Speech recognition not supported in this browser');
      return;
    }

    // Create new SpeechRecognition instance
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    // Set up event handlers
    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0])
        .map(result => result.transcript)
        .join('');
      
      setTranscript(transcript);
      
      // Reset the starting flag when we get results
      isStartingRef.current = false;
      
      // Check for voice commands to control sidebar
      const lowerTranscript = transcript.toLowerCase().trim();
      if (lowerTranscript === 'system close sidebar') {
        // Close sidebar for both mobile and desktop
        const mobileAlreadyClosed = !isSidebarOpen;
        const desktopAlreadyClosed = isDesktopSidebarCollapsed;
        
        setIsSidebarOpen(false);
        setIsDesktopSidebarCollapsed(true);
        
        // Provide contextual feedback
        if (mobileAlreadyClosed && desktopAlreadyClosed) {
          setNotification({
            message: 'Sidebar already closed',
            isVisible: true
          });
        } else {
          setNotification({
            message: 'Sidebar closed',
            isVisible: true
          });
        }
        setIsListening(false);
      } else if (lowerTranscript === 'system open sidebar') {
        // Open sidebar for both mobile and desktop
        const mobileAlreadyOpen = isSidebarOpen;
        const desktopAlreadyOpen = !isDesktopSidebarCollapsed;
        
        setIsSidebarOpen(true);
        setIsDesktopSidebarCollapsed(false);
        
        // Provide contextual feedback
        if (mobileAlreadyOpen && desktopAlreadyOpen) {
          setNotification({
            message: 'Sidebar already open',
            isVisible: true
          });
        } else {
          setNotification({
            message: 'Sidebar opened',
            isVisible: true
          });
        }
        setIsListening(false);
      }
    };

    recognition.onerror = (event: any) => {
      // Reset the starting flag on error
      isStartingRef.current = false;
      setIsListening(false);
      console.error('Speech recognition error', event.error);
    };

    recognition.onend = () => {
      // Reset the starting flag when recognition ends
      isStartingRef.current = false;
      setIsListening(false);
    };

    recognition.onstart = () => {
      // Reset the starting flag when recognition starts
      isStartingRef.current = false;
      setIsListening(true);
    };

    // Store reference to recognition instance
    speechRecognitionRef.current = recognition;

    // Cleanup function
    return () => {
      if (speechRecognitionRef.current) {
        try {
          // Reset the starting flag
          isStartingRef.current = false;
          speechRecognitionRef.current.stop();
        } catch (e) {
          console.warn('Error stopping speech recognition:', e);
        }
        speechRecognitionRef.current = null;
      }
    };
  }, []);

  const toggleVoiceRecognition = () => {
    // Check if browser supports SpeechRecognition
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.error('Speech recognition not supported in this browser');
      return;
    }

    if (!speechRecognitionRef.current) {
      console.error('Speech recognition not initialized properly');
      return;
    }

    if (isListening) {
      // Stop listening
      try {
        // Reset the starting flag when stopping
        isStartingRef.current = false;
        speechRecognitionRef.current.stop();
        setIsListening(false);
      } catch (error) {
        console.warn('Error stopping speech recognition:', error);
      }
    } else {
      // Start listening
      try {
        // Additional check to prevent InvalidStateError
        if (isStartingRef.current) {
          // Already starting, no need to start again
          return;
        }
        
        // Check if recognition is already running
        if (speechRecognitionRef.current.state === 'listening') {
          // Already listening, stop it first
          speechRecognitionRef.current.stop();
        }
        
        // Set the flag to indicate we're starting
        isStartingRef.current = true;
        speechRecognitionRef.current.start();
      } catch (error: any) {
        console.error('Error starting speech recognition:', error);
        // Reset the starting flag on error
        isStartingRef.current = false;
      }
    }
  };

  // Auto-dismiss notification after 3 seconds
  useEffect(() => {
    if (notification.isVisible) {
      const timer = setTimeout(() => {
        setNotification(prev => ({ ...prev, isVisible: false }));
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [notification.isVisible]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-center text-gray-900 dark:text-white mb-2">
          Voice Sidebar Control
        </h1>
        <p className="text-center text-gray-600 dark:text-gray-400 mb-8">
          Luxurious voice command interface with premium notifications
        </p>
        
        {/* Notification */}
        {notification.isVisible && (
          <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50
            px-6 py-4 rounded-2xl shadow-2xl backdrop-blur-md
            border transition-all duration-500
            bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 
            text-white border-gray-700/50 
            shadow-[0_0_30px_rgba(55,65,81,0.8)]
            flex items-center space-x-3
            min-w-[320px] animate-fade-in-down">
            <div className="flex-shrink-0 w-6 h-6 text-cyan-400">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                viewBox="0 0 24 24" 
                fill="currentColor"
                className="w-full h-full animate-pulse-slow"
              >
                <path d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm0 5a1 1 0 011-1h14a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1v-7zm2 2a1 1 0 000 2h2a1 1 0 000-2H6zm0 4a1 1 0 000 2h2a1 1 0 000-2H6zm4-4a1 1 0 000 2h6a1 1 0 000-2h-6zm0 4a1 1 0 000 2h6a1 1 0 000-2h-6z" />
                <path d="M19 5h2v14h-2a1 1 0 01-1-1V6a1 1 0 011-1z" />
              </svg>
            </div>
            <div className="font-medium text-lg">
              {notification.message}
            </div>
            <button 
              onClick={() => setNotification(prev => ({ ...prev, isVisible: false }))}
              className="ml-2 text-sm opacity-70 hover:opacity-100 focus:outline-none transition-opacity duration-200"
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
        )}
        
        {/* Luxurious Card */}
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-gray-200/30 dark:border-gray-700/30 mb-8 transition-all duration-300 hover:shadow-3xl">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-700 dark:from-blue-500 dark:to-indigo-600 shadow-lg mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.696.914 1.026a1 1 0 11-1.44 1.389c-.254-.269-.498-.546-.73-.832-.62-.772-1.258-1.564-1.71-2.574H5a1 1 0 110-2h1.252a17.04 17.04 0 01-.5-2H3a1 1 0 110-2h3V3a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98a1 1 0 11-1.79.895L16 15.382l-2.908 5.817a1 1 0 01-1.79-.894l.99-1.98.02-.038 2.992-5.98A1 1 0 0113 8z" clipRule="evenodd" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Premium Voice Control</h2>
            <p className="text-gray-600 dark:text-gray-400">Experience luxurious sidebar management with voice commands</p>
          </div>
          
          {/* Instructions */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-700 dark:to-gray-800 rounded-2xl p-6 mb-8 border border-blue-100 dark:border-gray-600">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              Voice Commands
            </h3>
            <ul className="space-y-3">
              <li className="flex items-start">
                <div className="flex-shrink-0 h-6 w-6 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center mt-0.5">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="ml-3 text-gray-700 dark:text-gray-300">Say <span className="font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">"system open sidebar"</span> to open the sidebar</span>
              </li>
              <li className="flex items-start">
                <div className="flex-shrink-0 h-6 w-6 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center mt-0.5">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <span className="ml-3 text-gray-700 dark:text-gray-300">Say <span className="font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">"system close sidebar"</span> to close the sidebar</span>
              </li>
            </ul>
          </div>
          
          {/* Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-700 dark:to-gray-800 rounded-2xl p-6 border border-gray-200/50 dark:border-gray-600 shadow-md">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                Voice Control
              </h3>
              <button
                onClick={toggleVoiceRecognition}
                className={`w-full py-4 rounded-2xl font-bold text-lg transition-all duration-300 flex items-center justify-center space-x-3 ${
                  isListening 
                    ? 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg shadow-red-500/30 transform scale-105' 
                    : 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white shadow-lg shadow-blue-500/30 hover:shadow-xl'
                }`}
              >
                {isListening ? (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                    </svg>
                    <span>Listening...</span>
                  </>
                ) : (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                    <span>Activate Voice</span>
                  </>
                )}
              </button>
            </div>
            
            <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-700 dark:to-gray-800 rounded-2xl p-6 border border-gray-200/50 dark:border-gray-600 shadow-md">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Manual Control
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setIsSidebarOpen(true)}
                  className="py-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-xl font-medium transition-all duration-300 shadow-md hover:shadow-lg flex items-center justify-center"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Open Mobile
                </button>
                
                <button
                  onClick={() => setIsSidebarOpen(false)}
                  className="py-3 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white rounded-xl font-medium transition-all duration-300 shadow-md hover:shadow-lg flex items-center justify-center"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Close Mobile
                </button>
                
                <button
                  onClick={() => setIsDesktopSidebarCollapsed(false)}
                  className="py-3 bg-gradient-to-r from-purple-500 to-violet-600 hover:from-purple-600 hover:to-violet-700 text-white rounded-xl font-medium transition-all duration-300 shadow-md hover:shadow-lg flex items-center justify-center"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Open Desktop
                </button>
                
                <button
                  onClick={() => setIsDesktopSidebarCollapsed(true)}
                  className="py-3 bg-gradient-to-r from-rose-500 to-pink-600 hover:from-rose-600 hover:to-pink-700 text-white rounded-xl font-medium transition-all duration-300 shadow-md hover:shadow-lg flex items-center justify-center"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Close Desktop
                </button>
              </div>
            </div>
          </div>
          
          {/* Status */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-gradient-to-br from-blue-50/50 to-indigo-50/50 dark:from-gray-700 dark:to-gray-800 rounded-2xl p-6 border border-blue-100/50 dark:border-gray-600">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                Mobile Sidebar
              </h3>
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-3 ${isSidebarOpen ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                <span className={`font-medium ${isSidebarOpen ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {isSidebarOpen ? 'Open' : 'Closed'}
                </span>
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-indigo-50/50 to-purple-50/50 dark:from-gray-700 dark:to-gray-800 rounded-2xl p-6 border border-indigo-100/50 dark:border-gray-600">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Desktop Sidebar
              </h3>
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-3 ${!isDesktopSidebarCollapsed ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                <span className={`font-medium ${!isDesktopSidebarCollapsed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {!isDesktopSidebarCollapsed ? 'Open' : 'Collapsed'}
                </span>
              </div>
            </div>
          </div>
          
          {/* Transcript */}
          <div className="bg-gradient-to-br from-gray-50 to-white dark:from-gray-700 dark:to-gray-800 rounded-2xl p-6 border border-gray-200/50 dark:border-gray-600">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Voice Transcript
            </h3>
            <div className="p-4 bg-gray-100 dark:bg-gray-700/50 rounded-xl min-h-[80px] border border-gray-200/50 dark:border-gray-600">
              <p className="text-gray-700 dark:text-gray-300 font-mono">
                {transcript || 'No speech detected yet...'}
              </p>
            </div>
          </div>
        </div>
        
        <div className="text-center text-gray-500 dark:text-gray-400 text-sm">
          Premium voice command interface with sophisticated notifications
        </div>
      </div>
    </div>
  );
}