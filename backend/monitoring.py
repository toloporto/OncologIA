import time
import psutil
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Métricas Prometheus
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
MODEL_INFERENCE_TIME = Histogram('model_inference_seconds', 'Model inference time')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage')
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage')

class MonitoringMiddleware:
    """Middleware para monitoring de la aplicación"""
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
            
        start_time = time.time()
        method = scope['method']
        path = scope['path']
        
        # Actualizar métricas de sistema
        MEMORY_USAGE.set(psutil.Process().memory_info().rss)
        CPU_USAGE.set(psutil.cpu_percent())
        
        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                status = message['status']
                REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()
                REQUEST_DURATION.observe(time.time() - start_time)
            await send(message)
            
        await self.app(scope, receive, send_wrapper)

def get_metrics():
    """Endpoint para métricas Prometheus"""
    return Response(generate_latest(), media_type="text/plain")