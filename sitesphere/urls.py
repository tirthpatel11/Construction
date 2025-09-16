"""
URL configuration for sitesphere project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from django.conf import settings
import os
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", lambda request: JsonResponse({"status": "ok"})),
    # Route root to the authentication login view to avoid duplicate namespace includes
    path("", RedirectView.as_view(pattern_name="authentication:login", permanent=False)),
    path("auth/", include("authentication.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("projects/", include("projects.urls")),
    path("engineering/", include("engineering.urls")),
    path("material-management/", include("material_management.urls")),
    path("accounts/", include("accounts.urls")),
    path("sales/", include("sales.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    frontend_index = os.path.join(settings.BASE_DIR, 'frontend', 'dist', 'index.html')
    if os.path.exists(frontend_index):
        urlpatterns += [
            path('', TemplateView.as_view(template_name='index.html')),
        ]
