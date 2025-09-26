"use client";

import { useEffect, useState } from 'react';

export default function DebugAPIPage() {
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    const testAPI = async () => {
      const newLogs = [];
      
      // Log the environment variable
      newLogs.push(`NEXT_PUBLIC_API_URL: ${process.env.NEXT_PUBLIC_API_URL}`);
      
      // Test direct fetch
      try {
        newLogs.push('Testing direct fetch to http://127.0.0.1:8000/api/chat/models...');
        const response = await fetch('http://127.0.0.1:8000/api/chat/models');
        newLogs.push(`Direct fetch status: ${response.status}`);
        
        if (response.ok) {
          const data = await response.json();
          newLogs.push(`Direct fetch success: ${data.models?.length || 0} models`);
        } else {
          newLogs.push(`Direct fetch failed: ${response.status} ${response.statusText}`);
        }
      } catch (error) {
        newLogs.push(`Direct fetch error: ${error.message}`);
      }
      
      // Test with localhost
      try {
        newLogs.push('Testing fetch to http://localhost:8000/api/chat/models...');
        const response = await fetch('http://localhost:8000/api/chat/models');
        newLogs.push(`Localhost fetch status: ${response.status}`);
        
        if (response.ok) {
          const data = await response.json();
          newLogs.push(`Localhost fetch success: ${data.models?.length || 0} models`);
        } else {
          newLogs.push(`Localhost fetch failed: ${response.status} ${response.statusText}`);
        }
      } catch (error) {
        newLogs.push(`Localhost fetch error: ${error.message}`);
      }
      
      setLogs(newLogs);
    };

    testAPI();
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">API Debug Page</h1>
      <div className="bg-gray-100 p-4 rounded">
        <h2 className="text-xl font-semibold mb-2">Debug Logs:</h2>
        <ul className="list-disc pl-5 space-y-2">
          {logs.map((log, index) => (
            <li key={index} className="font-mono text-sm">{log}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}