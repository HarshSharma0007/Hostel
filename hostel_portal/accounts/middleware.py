"""
Middleware — Catches ALL social auth exceptions and database errors.
Instead of showing an error page, redirects to landing with a query param.
"""
import logging
from django.shortcuts import redirect
from django.contrib.auth import logout as auth_logout
from django.conf import settings
from social_core.exceptions import AuthForbidden, AuthCanceled, AuthAlreadyAssociated, AuthUnknownError

logger = logging.getLogger(__name__)


class CustomSocialAuthExceptionMiddleware:
    """
    Catches every possible authentication / database error during the
    Google OAuth flow and redirects safely to the landing page.
    No error page, no 500, no stack trace — ever.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except (AuthForbidden, AuthCanceled, AuthAlreadyAssociated, AuthUnknownError) as e:
            logger.warning(f"[AUTH BLOCKED] {type(e).__name__}: {e}")
            # Log out any partially-created session
            if request.user.is_authenticated:
                auth_logout(request)
            return redirect('/?error=unauthorized')
        except Exception as e:
            # Catch database errors (ProgrammingError, OperationalError, etc.)
            # during the OAuth callback flow only
            if '/accounts/complete/' in request.path or '/accounts/login/' in request.path:
                logger.error(f"[CRITICAL AUTH ERROR] {type(e).__name__}: {e}")
                if request.user.is_authenticated:
                    auth_logout(request)
                return redirect('/?error=server')
            # Re-raise non-auth errors so Django handles them normally
            raise


class SafeNavigationMiddleware:
    """
    Enforces Role-Based Access Control (RBAC) across all system URLs.
    Prevents "URL molding" by redirecting unauthorized users back to safety.
    """

    PUBLIC_PATHS = ['/', '/login/', '/accounts/logout/']
    PUBLIC_PREFIXES = ['/accounts/login/', '/accounts/complete/', '/static/', '/media/', '/accounts/landing/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        user = request.user

        # 1. Allow Public Paths & Prefixes
        if path in self.PUBLIC_PATHS or any(path.startswith(p) for p in self.PUBLIC_PREFIXES):
            return self.get_response(request)

        # 2. Enforce Authentication
        if not user.is_authenticated:
            return redirect('/?error=unauthorized')

        # 3. Role-Based Access Enforcement
        email = user.email.lower().strip()

        # MASTER ADMIN ZONE
        if path.startswith('/master-admin/'):
            if email not in settings.ADMIN_EMAILS:
                return self._redirect_to_safety(request)

        # WARDEN ZONE
        elif path.startswith('/warden/'):
            if not hasattr(user, 'wardenprofile'):
                return self._redirect_to_safety(request)

        # FACULTY ZONE
        elif path.startswith('/faculty/'):
            if not hasattr(user, 'facultyprofile'):
                return self._redirect_to_safety(request)

        # STUDENT ZONE
        elif path.startswith('/accounts/dashboard/') or \
             path.startswith('/accounts/edit/') or \
             path.startswith('/complaints/student/'):
            if not hasattr(user, 'studentprofile'):
                return self._redirect_to_safety(request)

        return self.get_response(request)

    def _redirect_to_safety(self, request):
        """
        Intelligent redirection based on user role when they hit an unauthorized URL.
        """
        user = request.user
        email = user.email.lower()
        
        if email in settings.ADMIN_EMAILS:
            return redirect('/master-admin/dashboard/')
        if hasattr(user, 'wardenprofile'):
            return redirect('/warden/dashboard/')
        if hasattr(user, 'facultyprofile'):
            return redirect('/faculty/dashboard/')
        if hasattr(user, 'studentprofile'):
            return redirect('/accounts/dashboard/')
        
        # Absolute fallback
        auth_logout(request)
        return redirect('/?error=unauthorized')
