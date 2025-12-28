"""
Performance Monitoring for Hexashop
Real-time monitoring of API performance, database queries, and system health
"""
import time
import psutil
import threading
from datetime import datetime, timedelta
from collections import deque
import json

class PerformanceMonitor:
    def __init__(self, app=None):
        self.app = app
        self.request_times = deque(maxlen=1000)  # Last 1000 requests
        self.endpoint_stats = {}
        self.slow_requests = []  # Requests taking > 1 second
        self.error_counts = {}
        
        # System metrics
        self.cpu_usage = []
        self.memory_usage = []
        self.disk_io = []
        
        # Database metrics
        self.query_times = []
        self.slow_queries = []
        
        # Start monitoring thread
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self.monitor_thread.start()
    
    def init_app(self, app):
        self.app = app
    
    def record_request(self, endpoint, method, duration, status_code):
        """Record API request performance"""
        timestamp = datetime.utcnow()
        
        # Record request time
        self.request_times.append({
            'timestamp': timestamp.isoformat(),
            'endpoint': endpoint,
            'method': method,
            'duration': duration,
            'status': status_code
        })
        
        # Track endpoint statistics
        if endpoint not in self.endpoint_stats:
            self.endpoint_stats[endpoint] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'errors': 0,
                'slow_count': 0
            }
        
        stats = self.endpoint_stats[endpoint]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['avg_time'] = stats['total_time'] / stats['count']
        
        if duration > 1.0:  # Slow request threshold (1 second)
            stats['slow_count'] += 1
            self.slow_requests.append({
                'timestamp': timestamp.isoformat(),
                'endpoint': endpoint,
                'duration': duration,
                'method': method
            })
            # Keep only last 50 slow requests
            if len(self.slow_requests) > 50:
                self.slow_requests.pop(0)
        
        if status_code >= 400:
            stats['errors'] += 1
    
    def record_error(self, endpoint, error_type, error_message):
        """Record application errors"""
        if endpoint not in self.error_counts:
            self.error_counts[endpoint] = {}
        
        if error_type not in self.error_counts[endpoint]:
            self.error_counts[endpoint][error_type] = 0
        
        self.error_counts[endpoint][error_type] += 1
    
    def record_query(self, query, duration):
        """Record database query performance"""
        self.query_times.append({
            'timestamp': datetime.utcnow().isoformat(),
            'duration': duration,
            'query': query[:200]  # Store first 200 chars
        })
        
        # Keep only last 100 queries
        if len(self.query_times) > 100:
            self.query_times.pop(0)
        
        # Track slow queries (> 0.5 seconds)
        if duration > 0.5:
            self.slow_queries.append({
                'timestamp': datetime.utcnow().isoformat(),
                'duration': duration,
                'query': query[:200]
            })
            # Keep only last 20 slow queries
            if len(self.slow_queries) > 20:
                self.slow_queries.pop(0)
    
    def _monitor_system(self):
        """Background thread to monitor system resources"""
        while self.monitoring_active:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'percent': cpu_percent
                })
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.memory_usage.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'percent': memory.percent,
                    'used_gb': memory.used / (1024**3),
                    'total_gb': memory.total / (1024**3)
                })
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    self.disk_io.append({
                        'timestamp': datetime.utcnow().isoformat(),
                        'read_mb': disk_io.read_bytes / (1024**2),
                        'write_mb': disk_io.write_bytes / (1024**2)
                    })
                
                # Keep only last 60 data points (1 minute per point = 1 hour)
                for metric_list in [self.cpu_usage, self.memory_usage, self.disk_io]:
                    if len(metric_list) > 60:
                        metric_list.pop(0)
                
                # Sleep for monitoring interval
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"⚠️ Performance monitoring error: {e}")
                time.sleep(60)
    
    def get_summary(self):
        """Get performance summary"""
        # Calculate request statistics
        if self.request_times:
            durations = [req['duration'] for req in self.request_times]
            avg_response_time = sum(durations) / len(durations)
            max_response_time = max(durations)
            min_response_time = min(durations)
            
            # Calculate requests per minute
            recent_requests = [r for r in self.request_times 
                             if datetime.fromisoformat(r['timestamp']) > datetime.utcnow() - timedelta(minutes=1)]
            requests_per_minute = len(recent_requests)
        else:
            avg_response_time = max_response_time = min_response_time = 0
            requests_per_minute = 0
        
        # System metrics
        current_cpu = self.cpu_usage[-1]['percent'] if self.cpu_usage else 0
        current_memory = self.memory_usage[-1]['percent'] if self.memory_usage else 0
        
        # Error rate
        total_requests = sum(stats['count'] for stats in self.endpoint_stats.values())
        total_errors = sum(stats['errors'] for stats in self.endpoint_stats.values())
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'requests': {
                'total_last_hour': len(self.request_times),
                'per_minute': requests_per_minute,
                'avg_response_time_ms': round(avg_response_time * 1000, 2),
                'max_response_time_ms': round(max_response_time * 1000, 2),
                'min_response_time_ms': round(min_response_time * 1000, 2),
                'error_rate_percent': round(error_rate, 2)
            },
            'system': {
                'cpu_percent': current_cpu,
                'memory_percent': current_memory,
                'memory_used_gb': self.memory_usage[-1]['used_gb'] if self.memory_usage else 0,
                'memory_total_gb': self.memory_usage[-1]['total_gb'] if self.memory_usage else 0
            },
            'database': {
                'total_queries_tracked': len(self.query_times),
                'slow_queries': len(self.slow_queries),
                'avg_query_time_ms': round((sum(q['duration'] for q in self.query_times) / len(self.query_times) * 1000) if self.query_times else 0, 2)
            },
            'endpoints': {
                endpoint: {
                    'count': stats['count'],
                    'avg_time_ms': round(stats['avg_time'] * 1000, 2),
                    'error_count': stats['errors'],
                    'slow_count': stats['slow_count']
                }
                for endpoint, stats in sorted(self.endpoint_stats.items(), 
                                            key=lambda x: x[1]['count'], 
                                            reverse=True)[:10]  # Top 10 endpoints
            }
        }
    
    def get_health_status(self):
        """Get overall health status"""
        summary = self.get_summary()
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': []
        }
        
        # Check response times
        if summary['requests']['avg_response_time_ms'] > 1000:  # > 1 second
            health_status['checks'].append({
                'name': 'response_time',
                'status': 'warning',
                'message': f"High average response time: {summary['requests']['avg_response_time_ms']}ms"
            })
        else:
            health_status['checks'].append({
                'name': 'response_time',
                'status': 'healthy',
                'message': f"Good response time: {summary['requests']['avg_response_time_ms']}ms"
            })
        
        # Check error rate
        if summary['requests']['error_rate_percent'] > 5:  # > 5% error rate
            health_status['checks'].append({
                'name': 'error_rate',
                'status': 'warning',
                'message': f"High error rate: {summary['requests']['error_rate_percent']}%"
            })
        else:
            health_status['checks'].append({
                'name': 'error_rate',
                'status': 'healthy',
                'message': f"Low error rate: {summary['requests']['error_rate_percent']}%"
            })
        
        # Check system resources
        if summary['system']['cpu_percent'] > 80:
            health_status['checks'].append({
                'name': 'cpu',
                'status': 'warning',
                'message': f"High CPU usage: {summary['system']['cpu_percent']}%"
            })
        else:
            health_status['checks'].append({
                'name': 'cpu',
                'status': 'healthy',
                'message': f"CPU usage: {summary['system']['cpu_percent']}%"
            })
        
        if summary['system']['memory_percent'] > 85:
            health_status['checks'].append({
                'name': 'memory',
                'status': 'warning',
                'message': f"High memory usage: {summary['system']['memory_percent']}%"
            })
        else:
            health_status['checks'].append({
                'name': 'memory',
                'status': 'healthy',
                'message': f"Memory usage: {summary['system']['memory_percent']}%"
            })
        
        # Update overall status if any warnings
        if any(check['status'] == 'warning' for check in health_status['checks']):
            health_status['status'] = 'degraded'
        
        return health_status

# Global instance
performance_monitor = PerformanceMonitor()