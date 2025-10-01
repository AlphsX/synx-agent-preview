// Simple Node.js script to test API connectivity
async function testAPI() {
  try {
    console.log('Testing API connectivity...');
    
    const response = await fetch('http://127.0.0.1:8000/api/chat/models');
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('✅ Successfully fetched models:');
    console.log(`Total models: ${data.total_models}`);
    
    data.models.forEach((model, index) => {
      console.log(`  ${index + 1}. ${model.name} (${model.provider})`);
    });
    
  } catch (error) {
    console.error('❌ Error testing API:', error.message);
  }
}

testAPI();