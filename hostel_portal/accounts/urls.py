from django.urls import path
from .views import profile_edit, google_login_redirect, student_dashboard, custom_logout_view
from .views import login_redirect_view

urlpatterns = [
    path('login-redirect/', login_redirect_view, name='login_redirect'),
    path('dashboard/', student_dashboard, name='student_dashboard'),
    path('edit/', profile_edit, name='profile_edit'),
    path('logout/', custom_logout_view, name='logout'),
]
