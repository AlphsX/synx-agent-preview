# Comprehensive Error Handling and Monitoring System

This directory contains the comprehensive error handling and monitoring system for the AI Agent Backend. The system provides graceful degradation, structured logging, health checks, and retry logic with exponential backoff.

## Components

### 1. Error Handling (`error_handling.py`)

Provides comprehensive error handling with:

- **Graceful Degradation**: Automatic fallback when services fail
- **Retry Logic**: Exponential backoff with jitter for external API calls
- **Error Classification**: Standardized error codes and severity levels
- **Error Metrics**: Tracking and monitoring of error patterns
- **Structured Errors**: Consistent error response format

#### Key Classes:

- `ErrorMetrics`: Tracks error occurrences and service health
- `RetryConfig`: Configuration for retry logic with exponential backoff
- `GracefulDegradation`: Handles fallback mechanisms
- `StructuredError`: Standardized error response format

#### Usage Example:

```python
from app.core.error_handling import retry_with_backoff, RetryConfig, ServiceType

# Configure retry settings
retry_config = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
)

# Use retry logic
result = await retry_with_backoff(
    external_api_call,
    retry_config,
    ServiceType.SEARCH_API,
    *args, **kwargs
)
```

### 2. Health Checks (`health_checks.py`)

Comprehensive health monitoring for all services:

- **AI Services**: Groq, OpenAI, Anthropic
- **Search Services**: SerpAPI, Brave Search
- **Database Services**: PostgreSQL, Redis
- **Crypto Services**: Binance
- **Vector Database**: PostgreSQL with pgvector

#### Key Classes:

- `HealthCheckService`: Centralized health check management
- `HealthCheck`: Individual health check result
- `HealthStatus`: Health status enumeration

#### Usage Example:

```python
from app.core.health_checks import health_check_service

# Check all services
health_data = await health_check_service.check_all_services()

# Check specific service
health_check = await health_check_service.check_service("ai_groq")
```

### 3. Logging Middleware (`logging_middleware.py`)

Structured logging for all API requests and responses:

- **Request/Response Logging**: Complete API call tracking
- **External API Logging**: Track calls to external services
- **Performance Logging**: Monitor response times and metrics
- **Security Logging**: Track security-related events

#### Key Classes:

- `StructuredLogger`: Main logging interface
- `LoggingMiddleware`: FastAPI middleware for request/response logging
- `ExternalAPILogger`: Specialized logger for external API calls
- `PerformanceLogger`: Performance metrics logging

#### Usage Example:

```python
from app.core.logging_middleware import external_api_logger

# Track external API call
call_id = external_api_logger.start_call(
    service_name="serpapi",
    method="GET",
    url="https://serpapi.com/search",
    request_data={"query": "test"}
)

# Finish tracking
external_api_logger.finish_call(
    call_id=call_id,
    status_code=200,
    response_data={"results": 10}
)
```

## Health Check Endpoints

The system provides comprehensive health check endpoints:

### Core Health Endpoints

- `GET /api/health` - Overall system health
- `GET /api/health/status` - Simple health status for load balancers
- `GET /api/health/readiness` - Kubernetes readiness probe
- `GET /api/health/liveness` - Kubernetes liveness probe

### Service-Specific Health Endpoints

- `GET /api/health/ai` - AI services health
- `GET /api/health/search` - Search services health
- `GET /api/health/database` - Database services health
- `GET /api/health/services/{service_name}` - Individual service health

### Monitoring Endpoints

- `GET /api/health/errors` - Error metrics and monitoring
- `GET /api/health/performance` - Performance metrics
- `POST /api/health/errors/reset` - Reset error metrics

## Error Codes and Severity Levels

### Error Codes

- `API_TIMEOUT` - Request timeout
- `API_RATE_LIMIT` - Rate limit exceeded
- `API_AUTH_FAILED` - Authentication failed
- `API_UNAVAILABLE` - Service unavailable
- `API_INVALID_RESPONSE` - Invalid response format
- `SERVICE_DEGRADED` - Service operating in degraded mode
- `SERVICE_UNAVAILABLE` - Service completely unavailable
- `INVALID_INPUT` - Invalid input data
- `DATA_VALIDATION_FAILED` - Data validation error
- `INTERNAL_ERROR` - Internal system error
- `CONFIGURATION_ERROR` - Configuration issue

### Severity Levels

- `LOW` - Minor issues that don't affect functionality
- `MEDIUM` - Issues that may affect some functionality
- `HIGH` - Significant issues affecting core functionality
- `CRITICAL` - Critical issues requiring immediate attention

## Service Types

- `AI_MODEL` - AI model providers (Groq, OpenAI, Anthropic)
- `SEARCH_API` - Search services (SerpAPI, Brave Search)
- `CRYPTO_API` - Cryptocurrency services (Binance)
- `DATABASE` - Database services (PostgreSQL)
- `CACHE` - Cache services (Redis)
- `VECTOR_DB` - Vector database services
- `EXTERNAL_API` - Generic external API services

## Configuration

### Environment Variables

The system uses the following configuration from `settings`:

- `MAX_RETRIES` - Maximum retry attempts (default: 3)
- `RETRY_DELAY` - Base retry delay in seconds (default: 1)
- `EXTERNAL_API_TIMEOUT` - Timeout for external API calls (default: 30)
- `LOG_LEVEL` - Logging level (default: INFO)
- `LOG_FORMAT` - Log format (json or text)

### Retry Configuration

```python
retry_config = RetryConfig(
    max_retries=3,        # Maximum number of retries
    base_delay=1.0,       # Base delay in seconds
    max_delay=60.0,       # Maximum delay in seconds
    exponential_base=2.0, # Exponential backoff base
    jitter=True           # Add random jitter to delays
)
```

## Integration with Services

### Search Services

The search service (`search_service.py`) has been enhanced with:

- Retry logic for both SerpAPI and Brave Search
- Graceful fallback between providers
- Mock results when all providers fail
- Comprehensive error tracking and health monitoring

### AI Services

AI providers have been enhanced with:

- Retry logic for API calls
- Health checks for model availability
- Error classification and tracking
- Performance monitoring

### Crypto Services

The Binance service has been enhanced with:

- Retry logic for market data requests
- Health checks for API availability
- Error handling for rate limits and timeouts
- Performance tracking

## Monitoring and Alerting

### Error Metrics

The system tracks:

- Error counts by service and error code
- Error history with timestamps and details
- Service health status and consecutive failures
- Response times and performance metrics

### Health Monitoring

Health checks provide:

- Real-time service status
- Response time measurements
- Service availability tracking
- Overall system health assessment

### Performance Monitoring

Performance logging tracks:

- API response times
- Database query performance
- AI generation metrics
- Vector search performance
- External API call latencies

## Testing

Use the provided test script to verify the system:

```bash
python test_error_handling_monitoring.py
```

The test script covers:

- All health check endpoints
- Error handling and retry logic
- Service degradation scenarios
- Performance monitoring
- Error metrics collection

## Best Practices

### Error Handling

1. Always use structured errors for consistent responses
2. Classify errors appropriately for proper handling
3. Implement graceful degradation for critical services
4. Use retry logic for transient failures
5. Log errors with sufficient context for debugging

### Health Checks

1. Implement lightweight health checks for liveness probes
2. Use comprehensive health checks for readiness probes
3. Cache health check results to avoid overwhelming services
4. Provide detailed error messages for debugging
5. Monitor health check response times

### Logging

1. Use structured logging for better searchability
2. Sanitize sensitive data before logging
3. Include request IDs for tracing
4. Log performance metrics for monitoring
5. Use appropriate log levels for different events

### Performance

1. Monitor response times for all services
2. Track error rates and patterns
3. Use caching to reduce external API calls
4. Implement circuit breakers for failing services
5. Monitor resource usage and scaling needs

## Future Enhancements

Potential improvements to consider:

1. **Circuit Breaker Pattern**: Implement circuit breakers for failing services
2. **Distributed Tracing**: Add OpenTelemetry for distributed tracing
3. **Metrics Export**: Export metrics to Prometheus or similar systems
4. **Alerting**: Integrate with alerting systems (PagerDuty, Slack)
5. **Dashboard**: Create monitoring dashboards with Grafana
6. **Rate Limiting**: Implement intelligent rate limiting
7. **Caching**: Add intelligent caching for external API responses
8. **Load Balancing**: Implement load balancing for multiple service instances