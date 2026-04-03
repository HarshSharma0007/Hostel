"""
URL configuration for hostel_portal project.

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
from accounts.views import google_login_redirect, login_error  # ✅ Import here
from accounts.views import landing_page
urlpatterns = [
    path('', landing_page, name='landing_page'),  # ✅ Root route
    path('admin/', admin.site.urls),

    # 🔐 Google login and error at root level
    path('login/', google_login_redirect, name='google_login_redirect'),
    path('login-error/', login_error, name='login_error'),

    # 🔗 App-specific routes
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('social_django.urls', namespace='social')),
    path('complaints/', include('complaints.urls')), 

    path('warden/', include('warden.urls')),  # ✅ Warden app URLs
]

# 🖼️ Serving media files (Uploaded images) during development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# http://localhost:8000/accounts/login/google-oauth2/





