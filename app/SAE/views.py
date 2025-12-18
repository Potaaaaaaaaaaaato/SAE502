"""
Views for SAE502 Demo Application
"""

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def home(request):
    """Home page view"""
    context = {
        'title': 'SAE502',
    }
    return render(request, 'home.html', context)


def healthcheck(request):
    """
    Healthcheck endpoint for monitoring
    Returns status of Django, Database, and Redis
    """
    status = {
        'django': 'OK',
        'database': 'Unknown',
        'redis': 'Unknown',
        'timestamp': timezone.now().isoformat(),
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['database'] = 'OK'
    except Exception as e:
        status['database'] = f'ERROR: {str(e)}'
        logger.error(f"Database healthcheck failed: {e}")
    
    # Check Redis cache
    try:
        cache.set('healthcheck', 'OK', 10)
        if cache.get('healthcheck') == 'OK':
            status['redis'] = 'OK'
        else:
            status['redis'] = 'ERROR: Cannot read from cache'
    except Exception as e:
        status['redis'] = f'ERROR: {str(e)}'
        logger.error(f"Redis healthcheck failed: {e}")
    
    # Determine overall status
    overall_healthy = all(v == 'OK' for v in [status['django'], status['database'], status['redis']])
    status['status'] = 'healthy' if overall_healthy else 'unhealthy'
    
    response_status = 200 if overall_healthy else 503
    return JsonResponse(status, status=response_status)


def demo(request):
    """
    Demo page showing database and cache usage
    """
    # Visitor counter using cache
    visit_count = cache.get('visit_count', 0) + 1
    cache.set('visit_count', visit_count, None)  # Never expires
    
    context = {
        'title': 'Démonstration',
        'visit_count': visit_count,
        'timestamp': timezone.now(),
    }
    return render(request, 'demo.html', context)
