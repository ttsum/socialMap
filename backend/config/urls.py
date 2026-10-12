from django.urls import include, path
from django.http import JsonResponse
from django.db import connection


def healthz(request):
    database = 'ok'
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception:
        database = 'error'
    from django.conf import settings
    return JsonResponse({
        'status': 'ok' if database == 'ok' else 'degraded',
        'database': database,
        'aiConfigured': bool(__import__('os').getenv('ZHIPU_API_KEY')),
        'wechatConfigured': bool(__import__('os').getenv('WECHAT_APPSECRET')),
        'amapConfigured': bool(__import__('os').getenv('AMAP_API_KEY')),
        'model': __import__('os').getenv('LLM_MODEL', 'glm-5.3'),
    }, status=200 if database == 'ok' else 503)


urlpatterns = [
    path('healthz', healthz),
    path('api/v1/', include('activities.urls')),
    path('api/v1/', include('ai_service.urls')),
    path('api/v1/', include('users.urls')),
    path('api/v1/', include('locations.urls')),
]
