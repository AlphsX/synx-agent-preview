"use client";

import { useEffect, useState } from 'react';
import { chatAPI } from '@/lib/api';

export default function TestAPIPage() {
  const [models, setModels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        console.log('Testing API connection...');
        const response = await chatAPI.getModels();
        console.log('API Response:', response);
        setModels(response.models);
        setLoading(false);
      } catch (err) {
        console.error('API Error:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        setLoading(false);
      }
    };

    fetchModels();
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">API Test Page</h1>
      
      {loading && <p>Loading models...</p>}
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <p>Error: {error}</p>
        </div>
      )}
      
      {!loading && !error && (
        <div>
          <h2 className="text-xl font-semibold mb-2">Available Models ({models.length})</h2>
          <ul className="list-disc pl-5">
            {models.map((model, index) => (
              <li key={index} className="mb-2">
                <strong>{model.name}</strong> ({model.provider})
                <p className="text-gray-600 text-sm">{model.description}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}