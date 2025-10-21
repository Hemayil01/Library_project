from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

def return_all_links(request):
    return HttpResponse('<h2>API Links</h2><ul><li><a href="/api/books/">Books</a></li><li><a href="/api/copies/">Book Copies</a></li><li><a href="/auth/login/">Login</a></li><li><a href="/auth/register/">Register</a></li></ul>'
    )

urlpatterns = [
    path('', return_all_links),
    path('admin/', admin.site.urls),
    path('api/', include('book.urls')),
    path('auth/', include('user.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
