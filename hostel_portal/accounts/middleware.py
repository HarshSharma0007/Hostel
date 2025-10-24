from django.shortcuts import redirect
from social_core.exceptions import AuthForbidden

class CustomSocialAuthExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except AuthForbidden:
            return redirect('/login-error/')
