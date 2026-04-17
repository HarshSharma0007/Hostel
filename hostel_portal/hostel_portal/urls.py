"""
URL configuration for hostel_portal project.
"""
from django.urls import path, include
from accounts.views import google_login_redirect, landing_page

urlpatterns = [
    path('', landing_page, name='landing_page'),

    # Google login
    path('login/', google_login_redirect, name='google_login_redirect'),

    # App-specific routes
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('social_django.urls', namespace='social')),
    path('complaints/', include('complaints.urls')),
    path('warden/', include('warden.urls')),
    path('faculty/', include('faculty.urls')),
    path('master-admin/', include('master_admin.urls')),
]

handler404 = 'accounts.views.custom_404_view'
handler500 = 'accounts.views.custom_500_view'


# Serving media files during development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
