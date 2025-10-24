from django.urls import path
from .views import profile_edit, google_login_redirect, student_dashboard, login_error
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('dashboard/', student_dashboard, name='student_dashboard'),
    path('edit/', profile_edit, name='profile_edit'),
    # path('login/', google_login_redirect, name='google_login_redirect'),
    # path('login-error/', login_error, name='login_error'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

]
