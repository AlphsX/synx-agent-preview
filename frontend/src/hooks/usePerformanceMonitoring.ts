'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { performanceUtils } from '@/lib/markdown-utils';

export interface PerformanceMetrics {
  renderTimes: number[];
  averageRenderTime: number;
  cacheHitRate: number;
  errorCount: number;
  peakMemoryUsage: number;
  totalRenders: number;
}

export interface UsePerformanceMonitoringOptions {
  enabled?: boolean;
  reportInterval?: number;
  maxMetricsHistory?: number;
}

export function usePerformanceMonitoring(options: UsePerformanceMonitoringOptions = {}) {
  const {
    enabled = process.env.NODE_ENV === 'development',
    reportInterval = 30000, // 30 seconds
    maxMetricsHistory = 100
  } = options;

  const monitorRef = useRef(performanceUtils.createPerformanceMonitor());
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    renderTimes: [],
    averageRenderTime: 0,
    cacheHitRate: 0,
    errorCount: 0,
    peakMemoryUsage: 0,
    totalRenders: 0
  });

  // Performance monitoring functions
  const startRender = useCallback(() => {
    if (!enabled) return 0;
    return monitorRef.current.startRender();
  }, [enabled]);

  const endRender = useCallback((startTime: number, contentLength: number = 0) => {
    if (!enabled || startTime === 0) return 0;
    
    const renderTime = monitorRef.current.endRender(startTime, contentLength);
    monitorRef.current.recordMemoryUsage();
    
    return renderTime;
  }, [enabled]);

  const recordCacheHit = useCallback(() => {
    if (!enabled) return;
    monitorRef.current.recordCacheHit();
  }, [enabled]);

  const recordCacheMiss = useCallback(() => {
    if (!enabled) return;
    monitorRef.current.recordCacheMiss();
  }, [enabled]);

  const recordError = useCallback(() => {
    if (!enabled) return;
    monitorRef.current.recordError();
  }, [enabled]);

  // Update metrics periodically
  useEffect(() => {
    if (!enabled) return;

    const updateMetrics = () => {
      const currentMetrics = monitorRef.current.getMetrics();
      setMetrics({
        renderTimes: currentMetrics.renderTimes.slice(-maxMetricsHistory),
        averageRenderTime: currentMetrics.averageRenderTime,
        cacheHitRate: currentMetrics.cacheHitRate,
        errorCount: currentMetrics.errorCount,
        peakMemoryUsage: currentMetrics.peakMemoryUsage,
        totalRenders: currentMetrics.renderTimes.length
      });
    };

    // Initial update
    updateMetrics();

    // Set up periodic updates
    const interval = setInterval(updateMetrics, reportInterval);

    return () => clearInterval(interval);
  }, [enabled, reportInterval, maxMetricsHistory]);

  // Report performance issues
  useEffect(() => {
    if (!enabled || metrics.totalRenders < 10) return;

    // Report slow average render times
    if (metrics.averageRenderTime > 50) {
      console.warn(`Performance Warning: Average render time is ${metrics.averageRenderTime.toFixed(2)}ms`);
    }

    // Report low cache hit rates
    if (metrics.cacheHitRate < 0.7 && metrics.totalRenders > 20) {
      console.warn(`Performance Warning: Low cache hit rate: ${(metrics.cacheHitRate * 100).toFixed(1)}%`);
    }

    // Report high error rates
    if (metrics.errorCount > metrics.totalRenders * 0.1) {
      console.warn(`Performance Warning: High error rate: ${metrics.errorCount} errors in ${metrics.totalRenders} renders`);
    }

    // Report high memory usage (if available)
    if (metrics.peakMemoryUsage > 50 * 1024 * 1024) { // 50MB
      console.warn(`Performance Warning: High memory usage: ${(metrics.peakMemoryUsage / 1024 / 1024).toFixed(2)}MB`);
    }
  }, [enabled, metrics]);

  // Reset metrics
  const resetMetrics = useCallback(() => {
    if (!enabled) return;
    monitorRef.current.reset();
    setMetrics({
      renderTimes: [],
      averageRenderTime: 0,
      cacheHitRate: 0,
      errorCount: 0,
      peakMemoryUsage: 0,
      totalRenders: 0
    });
  }, [enabled]);

  // Get detailed performance report
  const getPerformanceReport = useCallback(() => {
    if (!enabled) return null;

    const currentMetrics = monitorRef.current.getMetrics();
    const cacheStats = performanceUtils.getCacheStats();

    return {
      rendering: {
        totalRenders: currentMetrics.renderTimes.length,
        averageRenderTime: currentMetrics.averageRenderTime,
        slowestRender: currentMetrics.renderTimes.length > 0 ? Math.max(...currentMetrics.renderTimes) : 0,
        fastestRender: currentMetrics.renderTimes.length > 0 ? Math.min(...currentMetrics.renderTimes) : 0
      },
      caching: {
        hitRate: currentMetrics.cacheHitRate,
        totalHits: currentMetrics.cacheHits,
        totalMisses: currentMetrics.cacheMisses,
        cacheUtilization: {
          featureAnalysis: `${cacheStats.featureAnalysis.size}/${cacheStats.featureAnalysis.maxSize}`,
          codeBlocks: `${cacheStats.codeBlocks.size}/${cacheStats.codeBlocks.maxSize}`,
          validation: `${cacheStats.validation.size}/${cacheStats.validation.maxSize}`
        }
      },
      errors: {
        totalErrors: currentMetrics.errorCount,
        errorRate: currentMetrics.renderTimes.length > 0 
          ? (currentMetrics.errorCount / currentMetrics.renderTimes.length * 100).toFixed(2) + '%'
          : '0%'
      },
      memory: {
        peakUsage: currentMetrics.peakMemoryUsage > 0 
          ? `${(currentMetrics.peakMemoryUsage / 1024 / 1024).toFixed(2)}MB`
          : 'N/A',
        currentUsage: 'memory' in performance 
          ? `${((performance as any).memory.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`
          : 'N/A'
      }
    };
  }, [enabled]);

  return {
    metrics,
    startRender,
    endRender,
    recordCacheHit,
    recordCacheMiss,
    recordError,
    resetMetrics,
    getPerformanceReport,
    enabled
  };
}

// Hook for component-level performance monitoring
export function useComponentPerformanceMonitoring(componentName: string) {
  const { startRender, endRender, recordError } = usePerformanceMonitoring();
  const renderStartRef = useRef<number>(0);

  const startComponentRender = useCallback(() => {
    renderStartRef.current = startRender();
  }, [startRender]);

  const endComponentRender = useCallback((contentLength?: number) => {
    if (renderStartRef.current > 0) {
      const renderTime = endRender(renderStartRef.current, contentLength);
      
      if (process.env.NODE_ENV === 'development' && renderTime > 16) { // 60fps threshold
        console.log(`${componentName} render: ${renderTime.toFixed(2)}ms`);
      }
      
      renderStartRef.current = 0;
      return renderTime;
    }
    return 0;
  }, [endRender, componentName]);

  const recordComponentError = useCallback((error: Error) => {
    recordError();
    
    if (process.env.NODE_ENV === 'development') {
      console.error(`${componentName} error:`, error);
    }
  }, [recordError, componentName]);

  return {
    startComponentRender,
    endComponentRender,
    recordComponentError
  };
}