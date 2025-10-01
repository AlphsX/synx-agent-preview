#!/usr/bin/env node

// Simple test script to verify backend integration
const API_BASE_URL = 'http://localhost:8000';

async function testBackendEndpoints() {
  console.log('🧪 Testing Backend Integration...\n');
  
  const tests = [
    {
      name: 'Health Check',
      url: `${API_BASE_URL}/health`,
      method: 'GET'
    },
    {
      name: 'Get Models',
      url: `${API_BASE_URL}/api/chat/models`,
      method: 'GET'
    },
    {
      name: 'Get Capabilities',
      url: `${API_BASE_URL}/api/chat/capabilities`,
      method: 'GET'
    },
    {
      name: 'Get Status',
      url: `${API_BASE_URL}/api/chat/status`,
      method: 'GET'
    },
    {
      name: 'Get Search Tools',
      url: `${API_BASE_URL}/api/chat/search-tools`,
      method: 'GET'
    }
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    try {
      console.log(`Testing: ${test.name}...`);
      const response = await fetch(test.url, { method: test.method });
      
      if (response.ok) {
        const data = await response.json();
        console.log(`✅ ${test.name} - OK`);
        console.log(`   Response: ${JSON.stringify(data).substring(0, 100)}...\n`);
        passed++;
      } else {
        console.log(`❌ ${test.name} - Failed (${response.status})`);
        failed++;
      }
    } catch (error) {
      console.log(`❌ ${test.name} - Error: ${error.message}`);
      failed++;
    }
  }

  // Test streaming chat
  console.log('Testing: Streaming Chat...');
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/conversations/test-123/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: 'Hello, this is a test message',
        model_id: 'openai/gpt-oss-120b'
      })
    });

    if (response.ok) {
      console.log('✅ Streaming Chat - OK');
      console.log('   Stream response received successfully\n');
      passed++;
    } else {
      console.log(`❌ Streaming Chat - Failed (${response.status})`);
      failed++;
    }
  } catch (error) {
    console.log(`❌ Streaming Chat - Error: ${error.message}`);
    failed++;
  }

  console.log(`\n📊 Test Results:`);
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`📈 Success Rate: ${Math.round((passed / (passed + failed)) * 100)}%`);

  if (failed === 0) {
    console.log('\n🎉 All tests passed! Backend integration is working correctly.');
    return true;
  } else {
    console.log('\n⚠️ Some tests failed. Please check the backend configuration.');
    return false;
  }
}

// Run the tests
testBackendEndpoints().then(success => {
  process.exit(success ? 0 : 1);
}).catch(error => {
  console.error('Test runner failed:', error);
  process.exit(1);
});