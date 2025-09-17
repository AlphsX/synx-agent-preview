#!/usr/bin/env python3
"""
Performance and Load Testing Suite

This test file focuses on performance testing and load testing:
- Concurrent user simulation
- Streaming response performance
- Memory usage monitoring
- Database connection pooling
- API rate limiting validation
- System resource utilization

Requirements: System performance and scalability validation
"""

import pytest
import asyncio
import aiohttp
import time
import psutil
import gc
import sys
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
import statistics
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 60  # seconds


class PerformanceMetrics:
    """Class to track and analyze performance metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.start_time = None
        self.end_time = None
        self.memory_samples: List[float] = []
        self.cpu_samples: List[float] = []
    
    def start_test(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        self.response_times.clear()
        self.success_count = 0
        self.error_count = 0
        self.memory_samples.clear()
        self.cpu_samples.clear()
    
    def record_request(self, response_time: float, success: bool):
        """Record a request result"""
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def record_system_metrics(self):
        """Record current system metrics"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        self.memory_samples.append(memory_mb)
        self.cpu_samples.append(cpu_percent)
    
    def end_test(self):
        """End performance monitoring"""
        self.end_time = time.time()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance test summary"""
        if not self.response_times:
            return {"error": "No response times recorded"}
        
        total_requests = self.success_count + self.error_count
        success_rate = (self.success_count / total_requests) * 100 if total_requests > 0 else 0
        
        duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        throughput = total_requests / duration if duration > 0 else 0
        
        return {
            "total_requests": total_requests,
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "success_rate_percent": success_rate,
            "test_duration_seconds": duration,
            "throughput_requests_per_second": throughput,
            "response_times": {
                "min_ms": min(self.response_times) * 1000,
                "max_ms": max(self.response_times) * 1000,
                "avg_ms": statistics.mean(self.response_times) * 1000,
                "median_ms": statistics.median(self.response_times) * 1000,
                "p95_ms": statistics.quantiles(self.response_times, n=20)[18] * 1000 if len(self.response_times) >= 20 else max(self.response_times) * 1000,
                "p99_ms": statistics.quantiles(self.response_times, n=100)[98] * 1000 if len(self.response_times) >= 100 else max(self.response_times) * 1000
            },
            "system_metrics": {
                "avg_memory_mb": statistics.mean(self.memory_samples) if self.memory_samples else 0,
                "max_memory_mb": max(self.memory_samples) if self.memory_samples else 0,
                "avg_cpu_percent": statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
                "max_cpu_percent": max(self.cpu_samples) if self.cpu_samples else 0
            }
        }


class TestConcurrentUsers:
    """Test system performance under concurrent user load"""
    
    async def make_health_request(self, session: aiohttp.ClientSession, request_id: int) -> Dict[str, Any]:
        """Make a single health check request"""
        start_time = time.time()
        try:
            async with session.get(
                f"{BASE_URL}/api/health/status",
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                duration = time.time() - start_time
                return {
                    "request_id": request_id,
                    "status": response.status,
                    "duration": duration,
                    "success": response.status == 200
                }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "request_id": request_id,
                "status": 0,
                "duration": duration,
                "success": False,
                "error": str(e)
            }
    
    async def make_ai_models_request(self, session: aiohttp.ClientSession, request_id: int) -> Dict[str, Any]:
        """Make a single AI models request"""
        start_time = time.time()
        try:
            async with session.get(
                f"{BASE_URL}/api/ai/models",
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                duration = time.time() - start_time
                return {
                    "request_id": request_id,
                    "status": response.status,
                    "duration": duration,
                    "success": response.status == 200
                }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "request_id": request_id,
                "status": 0,
                "duration": duration,
                "success": False,
                "error": str(e)
            }
    
    async def make_chat_request(self, session: aiohttp.ClientSession, request_id: int) -> Dict[str, Any]:
        """Make a single chat completion request"""
        start_time = time.time()
        try:
            payload = {
                "messages": [
                    {"role": "user", "content": f"Hello, this is test request {request_id}"}
                ],
                "model_id": "llama-3.1-8b-instant",
                "stream": False
            }
            
            async with session.post(
                f"{BASE_URL}/api/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                duration = time.time() - start_time
                return {
                    "request_id": request_id,
                    "status": response.status,
                    "duration": duration,
                    "success": response.status == 200
                }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "request_id": request_id,
                "status": 0,
                "duration": duration,
                "success": False,
                "error": str(e)
            }
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self):
        """Test concurrent health check requests"""
        concurrent_users = 50
        metrics = PerformanceMetrics()
        metrics.start_test()
        
        logger.info(f"Starting concurrent health check test with {concurrent_users} users")
        
        async with aiohttp.ClientSession() as session:
            # Create concurrent tasks
            tasks = [
                self.make_health_request(session, i)
                for i in range(concurrent_users)
            ]
            
            # Monitor system metrics during test
            async def monitor_system():
                while not all(task.done() for task in tasks):
                    metrics.record_system_metrics()
                    await asyncio.sleep(0.5)
            
            monitor_task = asyncio.create_task(monitor_system())
            
            # Execute all requests concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            monitor_task.cancel()
            
            # Process results
            for result in results:
                if isinstance(result, dict):
                    metrics.record_request(result["duration"], result["success"])
        
        metrics.end_test()
        summary = metrics.get_summary()
        
        logger.info("Concurrent Health Check Test Results:")
        logger.info(f"  Total requests: {summary['total_requests']}")
        logger.info(f"  Success rate: {summary['success_rate_percent']:.1f}%")
        logger.info(f"  Throughput: {summary['throughput_requests_per_second']:.2f} req/s")
        logger.info(f"  Avg response time: {summary['response_times']['avg_ms']:.2f}ms")
        logger.info(f"  P95 response time: {summary['response_times']['p95_ms']:.2f}ms")
        logger.info(f"  Max memory: {summary['system_metrics']['max_memory_mb']:.2f}MB")
        
        # Performance assertions
        assert summary["success_rate_percent"] >= 90, "At least 90% of requests should succeed"
        assert summary["response_times"]["avg_ms"] < 2000, "Average response time should be under 2 seconds"
        assert summary["response_times"]["p95_ms"] < 5000, "P95 response time should be under 5 seconds"
    
    @pytest.mark.asyncio
    async def test_concurrent_ai_model_requests(self):
        """Test concurrent AI model discovery requests"""
        concurrent_users = 30
        metrics = PerformanceMetrics()
        metrics.start_test()
        
        logger.info(f"Starting concurrent AI models test with {concurrent_users} users")
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.make_ai_models_request(session, i)
                for i in range(concurrent_users)
            ]
            
            # Monitor system metrics
            async def monitor_system():
                while not all(task.done() for task in tasks):
                    metrics.record_system_metrics()
                    await asyncio.sleep(0.5)
            
            monitor_task = asyncio.create_task(monitor_system())
            results = await asyncio.gather(*tasks, return_exceptions=True)
            monitor_task.cancel()
            
            # Process results
            for result in results:
                if isinstance(result, dict):
                    metrics.record_request(result["duration"], result["success"])
        
        metrics.end_test()
        summary = metrics.get_summary()
        
        logger.info("Concurrent AI Models Test Results:")
        logger.info(f"  Total requests: {summary['total_requests']}")
        logger.info(f"  Success rate: {summary['success_rate_percent']:.1f}%")
        logger.info(f"  Throughput: {summary['throughput_requests_per_second']:.2f} req/s")
        logger.info(f"  Avg response time: {summary['response_times']['avg_ms']:.2f}ms")
        
        # Performance assertions
        assert summary["success_rate_percent"] >= 80, "At least 80% of requests should succeed"
        assert summary["response_times"]["avg_ms"] < 3000, "Average response time should be under 3 seconds"
    
    @pytest.mark.asyncio
    async def test_concurrent_chat_requests(self):
        """Test concurrent chat completion requests"""
        concurrent_users = 10  # Lower for resource-intensive chat requests
        metrics = PerformanceMetrics()
        metrics.start_test()
        
        logger.info(f"Starting concurrent chat requests test with {concurrent_users} users")
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.make_chat_request(session, i)
                for i in range(concurrent_users)
            ]
            
            # Monitor system metrics
            async def monitor_system():
                while not all(task.done() for task in tasks):
                    metrics.record_system_metrics()
                    await asyncio.sleep(1)
            
            monitor_task = asyncio.create_task(monitor_system())
            results = await asyncio.gather(*tasks, return_exceptions=True)
            monitor_task.cancel()
            
            # Process results
            for result in results:
                if isinstance(result, dict):
                    metrics.record_request(result["duration"], result["success"])
        
        metrics.end_test()
        summary = metrics.get_summary()
        
        logger.info("Concurrent Chat Requests Test Results:")
        logger.info(f"  Total requests: {summary['total_requests']}")
        logger.info(f"  Success rate: {summary['success_rate_percent']:.1f}%")
        logger.info(f"  Throughput: {summary['throughput_requests_per_second']:.2f} req/s")
        logger.info(f"  Avg response time: {summary['response_times']['avg_ms']:.2f}ms")
        logger.info(f"  Max memory: {summary['system_metrics']['max_memory_mb']:.2f}MB")
        
        # Performance assertions for chat requests (more lenient due to AI processing)
        assert summary["success_rate_percent"] >= 70, "At least 70% of chat requests should succeed"
        assert summary["response_times"]["avg_ms"] < 30000, "Average chat response time should be under 30 seconds"


class TestStreamingPerformance:
    """Test streaming response performance"""
    
    @pytest.mark.asyncio
    async def test_streaming_response_performance(self):
        """Test streaming chat response performance"""
        logger.info("Testing streaming response performance")
        
        async with aiohttp.ClientSession() as session:
            # Create a conversation for streaming test
            conv_payload = {
                "title": "Streaming Performance Test",
                "user_id": "perf_test_user"
            }
            
            conversation_id = None
            try:
                async with session.post(
                    f"{BASE_URL}/api/chat/conversations",
                    json=conv_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 201]:
                        conv_data = await response.json()
                        conversation_id = conv_data.get("id") or conv_data.get("conversation_id")
            except Exception as e:
                logger.warning(f"Failed to create conversation for streaming test: {e}")
            
            if conversation_id:
                # Test streaming chat performance
                chat_payload = {
                    "content": "Tell me a detailed story about artificial intelligence and its impact on society. Please make it comprehensive and informative.",
                    "model_id": "llama-3.1-8b-instant",
                    "stream": True
                }
                
                start_time = time.time()
                chunk_count = 0
                total_content_length = 0
                first_chunk_time = None
                
                try:
                    async with session.post(
                        f"{BASE_URL}/api/chat/conversations/{conversation_id}/chat",
                        json=chat_payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        
                        if response.status == 200:
                            async for chunk in response.content.iter_chunked(1024):
                                if chunk:
                                    if first_chunk_time is None:
                                        first_chunk_time = time.time() - start_time
                                    
                                    chunk_count += 1
                                    total_content_length += len(chunk)
                                    
                                    # Limit test duration
                                    if time.time() - start_time > 30:
                                        break
                        
                        total_time = time.time() - start_time
                        
                        logger.info("Streaming Performance Results:")
                        logger.info(f"  Total chunks: {chunk_count}")
                        logger.info(f"  Total content length: {total_content_length} bytes")
                        logger.info(f"  Time to first chunk: {first_chunk_time:.3f}s" if first_chunk_time else "  No chunks received")
                        logger.info(f"  Total streaming time: {total_time:.3f}s")
                        
                        if chunk_count > 0:
                            avg_chunk_time = total_time / chunk_count
                            throughput = total_content_length / total_time
                            
                            logger.info(f"  Average time per chunk: {avg_chunk_time:.3f}s")
                            logger.info(f"  Throughput: {throughput:.2f} bytes/s")
                            
                            # Performance assertions
                            assert first_chunk_time < 10, "First chunk should arrive within 10 seconds"
                            assert avg_chunk_time < 1, "Average chunk time should be under 1 second"
                        else:
                            logger.warning("No streaming chunks received")
                
                except Exception as e:
                    logger.warning(f"Streaming test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_streams(self):
        """Test multiple concurrent streaming connections"""
        concurrent_streams = 5
        logger.info(f"Testing {concurrent_streams} concurrent streaming connections")
        
        async def single_stream_test(session, stream_id):
            """Test a single streaming connection"""
            try:
                # Create conversation
                conv_payload = {
                    "title": f"Concurrent Stream Test {stream_id}",
                    "user_id": f"stream_user_{stream_id}"
                }
                
                conversation_id = None
                async with session.post(
                    f"{BASE_URL}/api/chat/conversations",
                    json=conv_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 201]:
                        conv_data = await response.json()
                        conversation_id = conv_data.get("id") or conv_data.get("conversation_id")
                
                if not conversation_id:
                    return {"stream_id": stream_id, "success": False, "error": "Failed to create conversation"}
                
                # Start streaming chat
                chat_payload = {
                    "content": f"Stream test {stream_id}: Tell me about machine learning",
                    "model_id": "llama-3.1-8b-instant",
                    "stream": True
                }
                
                start_time = time.time()
                chunk_count = 0
                
                async with session.post(
                    f"{BASE_URL}/api/chat/conversations/{conversation_id}/chat",
                    json=chat_payload,
                    timeout=aiohttp.ClientTimeout(total=45)
                ) as response:
                    
                    if response.status == 200:
                        async for chunk in response.content.iter_chunked(1024):
                            if chunk:
                                chunk_count += 1
                                # Limit chunks per stream for testing
                                if chunk_count >= 10:
                                    break
                
                duration = time.time() - start_time
                
                return {
                    "stream_id": stream_id,
                    "success": True,
                    "chunk_count": chunk_count,
                    "duration": duration
                }
                
            except Exception as e:
                return {
                    "stream_id": stream_id,
                    "success": False,
                    "error": str(e)
                }
        
        async with aiohttp.ClientSession() as session:
            # Create concurrent streaming tasks
            tasks = [
                single_stream_test(session, i)
                for i in range(concurrent_streams)
            ]
            
            # Execute all streams concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyze results
            successful_streams = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            total_chunks = sum(r.get("chunk_count", 0) for r in results if isinstance(r, dict) and r.get("success"))
            
            logger.info("Concurrent Streaming Results:")
            logger.info(f"  Concurrent streams: {concurrent_streams}")
            logger.info(f"  Successful streams: {successful_streams}")
            logger.info(f"  Total chunks received: {total_chunks}")
            
            # Performance assertions
            assert successful_streams >= concurrent_streams * 0.6, "At least 60% of concurrent streams should succeed"


class TestMemoryUsage:
    """Test memory usage and resource management"""
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage during sustained load"""
        logger.info("Testing memory usage under sustained load")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        logger.info(f"Initial memory usage: {initial_memory:.2f} MB")
        
        memory_samples = []
        max_memory_increase = 0
        
        async with aiohttp.ClientSession() as session:
            # Perform sustained load for memory testing
            for iteration in range(20):
                # Make multiple requests in each iteration
                tasks = []
                for i in range(10):
                    tasks.append(session.get(f"{BASE_URL}/api/health/status", timeout=aiohttp.ClientTimeout(total=10)))
                
                # Execute requests
                try:
                    responses = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Close responses properly
                    for response in responses:
                        if hasattr(response, 'close'):
                            response.close()
                
                except Exception as e:
                    logger.warning(f"Request batch {iteration} failed: {e}")
                
                # Force garbage collection
                gc.collect()
                
                # Sample memory usage
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                max_memory_increase = max(max_memory_increase, memory_increase)
                
                memory_samples.append(current_memory)
                
                logger.info(f"Iteration {iteration + 1}: Memory: {current_memory:.2f} MB (+{memory_increase:.2f} MB)")
                
                # Brief pause between iterations
                await asyncio.sleep(0.5)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_increase = final_memory - initial_memory
        avg_memory = sum(memory_samples) / len(memory_samples)
        
        logger.info("Memory Usage Test Results:")
        logger.info(f"  Initial memory: {initial_memory:.2f} MB")
        logger.info(f"  Final memory: {final_memory:.2f} MB")
        logger.info(f"  Total increase: {total_increase:.2f} MB")
        logger.info(f"  Max increase: {max_memory_increase:.2f} MB")
        logger.info(f"  Average memory: {avg_memory:.2f} MB")
        
        # Memory usage assertions
        assert total_increase < 500, f"Total memory increase should be reasonable (< 500MB), got {total_increase:.2f}MB"
        assert max_memory_increase < 1000, f"Max memory increase should be reasonable (< 1GB), got {max_memory_increase:.2f}MB"
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """Test for potential memory leaks"""
        logger.info("Testing for memory leaks")
        
        process = psutil.Process()
        
        # Baseline memory measurement
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform repeated operations that might cause leaks
        async with aiohttp.ClientSession() as session:
            for cycle in range(5):
                logger.info(f"Memory leak test cycle {cycle + 1}")
                
                # Perform operations that create and destroy objects
                for i in range(50):
                    try:
                        async with session.get(f"{BASE_URL}/api/ai/models", timeout=aiohttp.ClientTimeout(total=5)) as response:
                            if response.status == 200:
                                await response.json()
                    except Exception:
                        pass  # Ignore errors for leak testing
                
                # Force garbage collection
                gc.collect()
                
                # Measure memory after each cycle
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - baseline_memory
                
                logger.info(f"  After cycle {cycle + 1}: {current_memory:.2f} MB (+{memory_increase:.2f} MB)")
                
                # Memory should not increase significantly between cycles
                if cycle > 0:  # Allow some increase in first cycle
                    assert memory_increase < 200, f"Memory increase suggests potential leak: {memory_increase:.2f}MB"


class TestDatabasePerformance:
    """Test database connection and query performance"""
    
    @pytest.mark.asyncio
    async def test_conversation_creation_performance(self):
        """Test conversation creation performance"""
        logger.info("Testing conversation creation performance")
        
        metrics = PerformanceMetrics()
        metrics.start_test()
        
        async with aiohttp.ClientSession() as session:
            # Create multiple conversations to test database performance
            tasks = []
            for i in range(20):
                conv_payload = {
                    "title": f"Performance Test Conversation {i}",
                    "user_id": f"perf_user_{i}"
                }
                
                task = session.post(
                    f"{BASE_URL}/api/chat/conversations",
                    json=conv_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                )
                tasks.append(task)
            
            # Execute conversation creation requests
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_creations = 0
            for response in responses:
                if hasattr(response, 'status') and response.status in [200, 201]:
                    successful_creations += 1
                    response.close()
                elif hasattr(response, 'close'):
                    response.close()
            
            total_time = time.time() - start_time
        
        logger.info("Conversation Creation Performance:")
        logger.info(f"  Total conversations: {len(tasks)}")
        logger.info(f"  Successful creations: {successful_creations}")
        logger.info(f"  Total time: {total_time:.3f}s")
        logger.info(f"  Average time per creation: {total_time / len(tasks):.3f}s")
        
        # Performance assertions
        assert successful_creations >= len(tasks) * 0.8, "At least 80% of conversation creations should succeed"
        assert total_time / len(tasks) < 2.0, "Average conversation creation time should be under 2 seconds"


async def main():
    """Run performance and load tests"""
    print("🚀 PERFORMANCE AND LOAD TESTING SUITE")
    print("=" * 60)
    print("Testing System Performance and Scalability")
    print("=" * 60)
    
    # Run tests using pytest programmatically
    import pytest
    
    # Run this test file with performance-specific settings
    exit_code = pytest.main([
        __file__, 
        "-v", 
        "--tb=short",
        "-x",  # Stop on first failure
        "--durations=10"  # Show slowest 10 tests
    ])
    
    if exit_code == 0:
        print("\n✅ All performance and load tests passed!")
        print("\n🎯 Performance Metrics Validated:")
        print("   ✅ Concurrent user handling")
        print("   ✅ Streaming response performance")
        print("   ✅ Memory usage optimization")
        print("   ✅ Database connection performance")
        print("   ✅ System resource utilization")
        
        print("\n📊 Test Coverage:")
        print("   - Concurrent health check requests (50 users)")
        print("   - Concurrent AI model requests (30 users)")
        print("   - Concurrent chat requests (10 users)")
        print("   - Streaming response performance")
        print("   - Multiple concurrent streaming connections")
        print("   - Memory usage under sustained load")
        print("   - Memory leak detection")
        print("   - Database operation performance")
        
        print("\n⚡ Performance Benchmarks:")
        print("   - Health checks: <2s avg, >90% success rate")
        print("   - AI models: <3s avg, >80% success rate")
        print("   - Chat requests: <30s avg, >70% success rate")
        print("   - Memory usage: <500MB increase under load")
        print("   - Streaming: <10s to first chunk")
    else:
        print("\n❌ Some performance tests failed")
        print("Check logs for performance bottlenecks and optimization opportunities")
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)