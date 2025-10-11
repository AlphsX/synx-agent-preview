# Groq Compound Model Integration

This document describes the integration of Groq's compound model for URL-based queries and website analysis.

## Overview

The Groq compound model is a specialized AI model that can visit websites and analyze their content. When users include URLs in their messages, the system automatically detects them and uses the compound model to provide comprehensive analysis and summaries.

## Features

### Automatic URL Detection

The system uses regex patterns to detect various URL formats:

- Standard HTTP/HTTPS URLs: `https://example.com`
- www URLs without protocol: `www.example.com`
- Domain URLs: `example.com`

### Intelligent Model Selection

When URLs are detected in a user message, the system:

1. Checks if the Groq compound model is available
2. Automatically switches to the compound model for processing
3. Falls back to regular AI models if compound model fails

### Real-time Website Analysis

The compound model can:

- Visit and analyze webpage content
- Summarize key points from articles
- Answer specific questions about website content
- Extract relevant information based on user queries

## API Endpoints

### Check Service Status

```http
GET /api/v1/external/groq-compound/status
```

**Response:**

```json
{
  "available": true,
  "model": "groq/compound",
  "timeout": 120,
  "max_retries": 3
}
```

### Chat with URL Detection

```http
POST /api/v1/external/groq-compound/chat-with-urls
```

**Parameters:**

- `message` (required): Message that may contain URLs
- `conversation_history` (optional): Previous conversation messages

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/external/groq-compound/chat-with-urls" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze this page: https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed"
  }'
```

**Response:**

```json
{
  "message": "Analyze this page: https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed",
  "should_use_compound": true,
  "detected_urls": [
    "https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed"
  ],
  "response": "This article discusses Groq's Language Processing Unit (LPU)...",
  "model": "groq/compound"
}
```

### Direct URL Analysis

```http
POST /api/v1/external/groq-compound/analyze-url
```

**Parameters:**

- `url` (required): URL to analyze
- `question` (optional): Specific question about the URL

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/external/groq-compound/analyze-url?url=https://groq.com&question=What%20are%20the%20key%20features%20of%20Groq?" \
  -H "Content-Type: application/json"
```

**Response:**

```json
{
  "url": "https://groq.com",
  "question": "What are the key features of Groq?",
  "analysis": "Based on the Groq website, the key features include...",
  "model": "groq/compound"
}
```

### URL Detection Utility

```http
GET /api/v1/external/groq-compound/detect-urls
```

**Parameters:**

- `text` (required): Text to analyze for URLs

**Response:**

```json
{
  "text": "Check out https://groq.com and www.example.com",
  "detected_urls": ["https://groq.com", "https://www.example.com"],
  "should_use_compound": true,
  "url_count": 2
}
```

## Integration with Enhanced Chat

The compound model is automatically integrated into the enhanced chat service. When a user sends a message containing URLs:

1. The system detects URLs using regex patterns
2. If URLs are found, it switches to the compound model
3. The compound model visits the URLs and analyzes their content
4. The response includes both the analysis and regular conversation context

### Example Usage in Chat

```python
# User message with URL
message = "Summarize the key points of this article: https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed"

# System automatically detects URL and uses compound model
async for chunk in chat_service.generate_ai_response(
    message=message,
    model_id="groq/compound",  # Will be automatically selected
    user_context=user_context
):
    print(chunk, end="", flush=True)
```

## Configuration

### Environment Variables

```bash
# Required for compound model functionality
GROQ_API_KEY=your_groq_api_key_here
```

### Service Configuration

The compound service can be configured in `backend/app/external_apis/groq_compound_service.py`:

```python
class GroqCompoundService:
    def __init__(self):
        self.compound_model = "groq/compound"
        self.timeout = 120  # Longer timeout for web browsing
        self.max_retries = 3
```

## Error Handling

The system includes comprehensive error handling:

1. **API Key Missing**: Returns error message about missing configuration
2. **Network Errors**: Automatic retry with exponential backoff
3. **Rate Limits**: Respects Groq API rate limits with appropriate delays
4. **Timeout Errors**: Graceful handling of slow website responses
5. **Fallback**: Falls back to regular AI models if compound model fails

## Testing

### Backend Testing

Run the test script to verify functionality:

```bash
cd backend
python test_groq_compound.py
```

### Frontend Testing

Visit the test page to interact with the compound model:

```
http://localhost:3000/test-compound-model
```

## Best Practices

1. **URL Validation**: Always validate URLs before processing
2. **Timeout Handling**: Use appropriate timeouts for web requests
3. **Rate Limiting**: Respect API rate limits and implement backoff
4. **Error Messages**: Provide clear error messages to users
5. **Fallback Strategy**: Always have a fallback when compound model fails

## Limitations

1. **API Key Required**: Requires valid Groq API key with compound model access
2. **Rate Limits**: Subject to Groq API rate limits
3. **Website Accessibility**: Can only analyze publicly accessible websites
4. **Response Time**: May be slower than regular models due to web browsing
5. **Content Limitations**: Limited by website structure and content accessibility

## Future Enhancements

1. **Caching**: Cache website analysis to improve performance
2. **Batch Processing**: Support multiple URLs in a single request
3. **Content Filtering**: Filter inappropriate or irrelevant content
4. **Custom Instructions**: Allow custom analysis instructions per URL
5. **Integration**: Deeper integration with vector database for content storage
