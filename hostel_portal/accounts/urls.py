from django.urls import path
from .views import profile_edit, google_login_redirect, student_dashboard

urlpatterns = [
    path('dashboard/', student_dashboard, name='student_dashboard'),
    path('edit/', profile_edit, name='profile_edit'),
    path('login/', google_login_redirect, name='google_login_redirect'),
]
