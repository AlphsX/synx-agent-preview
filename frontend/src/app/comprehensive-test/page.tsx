"use client";

import { useEffect, useState } from 'react';

export default function ComprehensiveTestPage() {
  const [testResults, setTestResults] = useState<any[]>([]);
  const [currentTest, setCurrentTest] = useState<string>('');

  useEffect(() => {
    const runTests = async () => {
      const results: any[] = [];
      
      // Test 1: Environment variables
      setCurrentTest('Checking environment variables...');
      results.push({
        test: 'Environment Variables',
        status: 'info',
        message: `NEXT_PUBLIC_API_URL: ${process.env.NEXT_PUBLIC_API_URL || 'Not set'}`
      });
      
      // Test 2: Direct fetch to 127.0.0.1
      try {
        setCurrentTest('Testing direct fetch to 127.0.0.1:8000...');
        const response = await fetch('http://127.0.0.1:8000/api/chat/models');
        results.push({
          test: 'Direct Fetch (127.0.0.1)',
          status: response.ok ? 'success' : 'error',
          message: response.ok ? `Success: ${response.status}` : `Error: ${response.status} ${response.statusText}`
        });
        
        if (response.ok) {
          const data = await response.json();
          results.push({
            test: 'Data Parsing',
            status: 'success',
            message: `Found ${data.models?.length || 0} models`
          });
        }
      } catch (error) {
        results.push({
          test: 'Direct Fetch (127.0.0.1)',
          status: 'error',
          message: `Exception: ${error.message}`
        });
      }
      
      // Test 3: Direct fetch to localhost
      try {
        setCurrentTest('Testing direct fetch to localhost:8000...');
        const response = await fetch('http://localhost:8000/api/chat/models');
        results.push({
          test: 'Direct Fetch (localhost)',
          status: response.ok ? 'success' : 'error',
          message: response.ok ? `Success: ${response.status}` : `Error: ${response.status} ${response.statusText}`
        });
      } catch (error) {
        results.push({
          test: 'Direct Fetch (localhost)',
          status: 'error',
          message: `Exception: ${error.message}`
        });
      }
      
      // Test 4: Using the chatAPI implementation
      try {
        setCurrentTest('Testing chatAPI implementation...');
        // Dynamically import the API to avoid SSR issues
        const { chatAPI } = await import('@/lib/api');
        
        const response = await chatAPI.getModels();
        results.push({
          test: 'chatAPI Implementation',
          status: 'success',
          message: `Success: Found ${response.models.length} models`
        });
      } catch (error) {
        results.push({
          test: 'chatAPI Implementation',
          status: 'error',
          message: `Exception: ${error.message}`
        });
      }
      
      setTestResults(results);
      setCurrentTest('Tests completed');
    };

    runTests();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'bg-green-100 text-green-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'info': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Comprehensive API Test</h1>
      
      <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="font-medium">Current Test: {currentTest}</p>
      </div>
      
      <div className="space-y-4">
        {testResults.map((result, index) => (
          <div 
            key={index} 
            className={`p-4 rounded-lg border ${result.status === 'success' ? 'border-green-200' : result.status === 'error' ? 'border-red-200' : 'border-blue-200'}`}
          >
            <div className="flex justify-between items-center">
              <h3 className="font-semibold">{result.test}</h3>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(result.status)}`}>
                {result.status.toUpperCase()}
              </span>
            </div>
            <p className="mt-2 text-gray-700">{result.message}</p>
          </div>
        ))}
      </div>
      
      {testResults.length > 0 && (
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h2 className="text-xl font-semibold mb-3">Debug Information</h2>
          <p className="text-sm text-gray-600">
            If you're seeing this page, it means the frontend is working but there might be an issue with 
            the API connection. Check the results above to identify the problem.
          </p>
        </div>
      )}
    </div>
  );
}