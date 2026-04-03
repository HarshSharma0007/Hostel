from django.urls import path
from .views import profile_edit, google_login_redirect, student_dashboard, login_error, custom_logout_view
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from .views import login_redirect_view
urlpatterns = [
    path('login-redirect/', login_redirect_view, name='login_redirect'),
    path('dashboard/', student_dashboard, name='student_dashboard'),
    path('edit/', profile_edit, name='profile_edit'),
    # path('login/', google_login_redirect, name='google_login_redirect'),
    # path('login-error/', login_error, name='login_error'),
    path('logout/', custom_logout_view, name='logout'),
    

    # path('landing/', landing_page, name='landing_page'),


]
