#!/usr/bin/env python3
"""
Performance Optimization Module for PENIN-Ω

This module provides performance optimizations including:
- Caching mechanisms
- Resource monitoring optimization
- Computational efficiency improvements
- Memory management
"""

import threading
import time
import weakref
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache, wraps
from typing import Any


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""

    cache_hits: int = 0
    cache_misses: int = 0
    total_computation_time: float = 0.0
    last_update: float = 0.0

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


class PerformanceOptimizer:
    """Main performance optimizer class"""

    def __init__(self, cache_ttl: float = 60.0, max_cache_size: int = 128):
        self.cache_ttl = cache_ttl
        self.max_cache_size = max_cache_size
        self.metrics = PerformanceMetrics()
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = threading.RLock()

    def cached(self, ttl: float | None = None, key_func: Callable | None = None):
        """Decorator for caching function results"""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

                with self._lock:
                    current_time = time.time()

                    # Check cache
                    if cache_key in self._cache:
                        result, timestamp = self._cache[cache_key]
                        cache_ttl_actual = ttl or self.cache_ttl

                        if current_time - timestamp < cache_ttl_actual:
                            self.metrics.cache_hits += 1
                            return result
                        else:
                            # Expired cache entry
                            del self._cache[cache_key]

                    self.metrics.cache_misses += 1

                # Compute result
                start_time = time.time()
                result = func(*args, **kwargs)
                computation_time = time.time() - start_time

                # Cache result
                with self._lock:
                    self.metrics.total_computation_time += computation_time
                    self.metrics.last_update = current_time

                    # Clean up old entries if cache is full
                    if len(self._cache) >= self.max_cache_size:
                        # Remove oldest entries (simple FIFO)
                        oldest_keys = sorted(
                            self._cache.keys(), key=lambda k: self._cache[k][1]
                        )[: len(self._cache) - self.max_cache_size + 1]
                        for key in oldest_keys:
                            del self._cache[key]

                    self._cache[cache_key] = (result, current_time)

                return result

            return wrapper

        return decorator

    def clear_cache(self):
        """Clear all cached results"""
        with self._lock:
            self._cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                "cache_size": len(self._cache),
                "cache_hit_rate": self.metrics.cache_hit_rate,
                "total_computation_time": self.metrics.total_computation_time,
                "last_update": self.metrics.last_update,
            }


class ResourceMonitor:
    """Optimized resource monitoring with caching"""

    def __init__(self, update_interval: float = 5.0):
        self.update_interval = update_interval
        self._last_update = 0.0
        self._cached_values: dict[str, float] = {}
        self._lock = threading.RLock()

    def get_cpu_usage(self) -> float:
        """Get CPU usage with caching"""
        return self._get_cached_resource("cpu", self._measure_cpu)

    def get_memory_usage(self) -> float:
        """Get memory usage with caching"""
        return self._get_cached_resource("memory", self._measure_memory)

    def _get_cached_resource(
        self, resource_name: str, measure_func: Callable[[], float]
    ) -> float:
        """Get cached resource value or measure new one"""
        with self._lock:
            current_time = time.time()

            if (
                resource_name not in self._cached_values
                or current_time - self._last_update > self.update_interval
            ):
                self._cached_values[resource_name] = measure_func()
                self._last_update = current_time

            return self._cached_values[resource_name]

    def _measure_cpu(self) -> float:
        """Measure CPU usage"""
        try:
            import psutil

            return psutil.cpu_percent(interval=None) / 100.0
        except ImportError:
            return 0.99  # Fail-closed

    def _measure_memory(self) -> float:
        """Measure memory usage"""
        try:
            import psutil

            return psutil.virtual_memory().percent / 100.0
        except ImportError:
            return 0.99  # Fail-closed


class ComputationalOptimizer:
    """Computational efficiency optimizations"""

    @staticmethod
    @lru_cache(maxsize=256)
    def fast_hash(data: str) -> int:
        """Fast hash function with caching"""
        return hash(data)

    @staticmethod
    def batch_process(
        items: list, batch_size: int = 100, process_func: Callable = None
    ):
        """Process items in batches for efficiency"""
        if not process_func:
            return items

        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batch_result = process_func(batch)
            if isinstance(batch_result, list):
                results.extend(batch_result)
            else:
                results.append(batch_result)

        return results

    @staticmethod
    def optimize_list_operations(data: list) -> list:
        """Optimize common list operations"""
        # Remove duplicates while preserving order
        seen = set()
        optimized = []
        for item in data:
            if item not in seen:
                seen.add(item)
                optimized.append(item)
        return optimized


class MemoryManager:
    """Memory management utilities"""

    def __init__(self, max_memory_mb: int = 512):
        self.max_memory_mb = max_memory_mb
        self._weak_refs: weakref.WeakSet = weakref.WeakSet()

    def track_object(self, obj: Any):
        """Track object for memory management"""
        self._weak_refs.add(obj)

    def cleanup_unused(self):
        """Clean up unused objects"""
        # WeakSet automatically removes dead references
        # This is just a placeholder for more complex cleanup logic
        pass

    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0


# Global performance optimizer instance
_performance_optimizer = PerformanceOptimizer()
_resource_monitor = ResourceMonitor()
_memory_manager = MemoryManager()


def cached(ttl: float | None = None, key_func: Callable | None = None):
    """Global cached decorator"""
    return _performance_optimizer.cached(ttl, key_func)


def get_cpu_usage() -> float:
    """Get cached CPU usage"""
    return _resource_monitor.get_cpu_usage()


def get_memory_usage() -> float:
    """Get cached memory usage"""
    return _resource_monitor.get_memory_usage()


def get_performance_stats() -> dict[str, Any]:
    """Get performance statistics"""
    return {
        "cache_stats": _performance_optimizer.get_cache_stats(),
        "memory_usage_mb": _memory_manager.get_memory_usage_mb(),
        "resource_cache": {
            "cpu": _resource_monitor.get_cpu_usage(),
            "memory": _resource_monitor.get_memory_usage(),
        },
    }


def clear_performance_cache():
    """Clear all performance caches"""
    _performance_optimizer.clear_cache()
    _memory_manager.cleanup_unused()
