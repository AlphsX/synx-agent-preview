"use client";

import { useEffect, useState } from 'react';

export default function NetworkTestPage() {
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const testNetwork = async () => {
      try {
        console.log('Starting network test...');
        
        // Test 1: Fetch from 127.0.0.1
        console.log('Testing 127.0.0.1:8000...');
        const response1 = await fetch('http://127.0.0.1:8000/api/chat/models');
        console.log('127.0.0.1 response:', response1.status, response1.statusText);
        
        if (response1.ok) {
          const data1 = await response1.json();
          console.log('127.0.0.1 data:', data1);
          setResults({
            success: true,
            data: data1,
            endpoint: 'http://127.0.0.1:8000/api/chat/models'
          });
        } else {
          throw new Error(`127.0.0.1 failed with status ${response1.status}`);
        }
      } catch (err) {
        console.error('Network test error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    testNetwork();
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Network Test</h1>
      
      {loading && <p className="text-blue-500">Testing network connectivity...</p>}
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <p><strong>Error:</strong> {error}</p>
        </div>
      )}
      
      {results && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          <p><strong>Success!</strong> Connected to {results.endpoint}</p>
          <p>Found {results.data.models.length} models:</p>
          <ul className="list-disc pl-5 mt-2">
            {results.data.models.map((model: any, index: number) => (
              <li key={index}>
                <strong>{model.name}</strong> ({model.provider}) - {model.description}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}