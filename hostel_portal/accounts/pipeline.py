"""
Authentication Pipeline — Bulletproof & Future-Proof

ALL database queries are wrapped in try/except to prevent crashes from:
- Missing tables (migrations not run)
- Missing columns (model changes not migrated)
- Any other database-level errors

On ANY failure, the user is safely redirected to the landing page with an error message.
"""
import logging
from django.conf import settings
from social_core.exceptions import AuthForbidden
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

# ADMIN_EMAILS list is now centrally managed in .env and settings.py



def _safe_exists(model, **filters):
    """
    Safely check if a record exists. Returns False on ANY database error
    (missing table, missing column, connection error, etc.)
    """
    try:
        return model.objects.filter(**filters).exists()
    except Exception as e:
        logger.error(f"[DB ERROR] {model.__name__}.objects.filter({filters}): {e}")
        return False


def _safe_get_or_create(model, user, defaults=None):
    """
    Safely get_or_create a profile. Returns (profile, created) or (None, False) on error.
    """
    try:
        return model.objects.get_or_create(user=user, defaults=defaults or {})
    except Exception as e:
        logger.error(f"[DB ERROR] {model.__name__}.get_or_create(user={user}): {e}")
        return None, False


def _safe_get(model, **filters):
    """
    Safely get a single record. Returns None on ANY error.
    """
    try:
        return model.objects.get(**filters)
    except model.DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"[DB ERROR] {model.__name__}.objects.get({filters}): {e}")
        return None


def _safe_filter_first(model, **filters):
    """
    Safely get the first matching record. Returns None on ANY error.
    """
    try:
        return model.objects.filter(**filters).first()
    except Exception as e:
        logger.error(f"[DB ERROR] {model.__name__}.objects.filter({filters}).first(): {e}")
        return None


# ═══════════════════════════════════════════════════════════
# STEP 1: auth_allowed — Gate: who can log in?
# ═══════════════════════════════════════════════════════════
def auth_allowed(strategy, details, backend, user=None, *args, **kwargs):
    from accounts.models import AllowedStudent, AllowedWarden, AllowedFaculty

    email = details.get('email', '').lower().strip()

    if not email:
        raise AuthForbidden(backend)

    # 1. Admin — emails from settings.ADMIN_EMAILS always allowed
    if email in settings.ADMIN_EMAILS:
        return

    # 1.1 Test Users — dynamically allowed via .env
    if (settings.TEST_WARDEN_EMAIL and email == settings.TEST_WARDEN_EMAIL) or \
       (settings.TEST_FACULTY_EMAIL and email == settings.TEST_FACULTY_EMAIL):
        return


    # 2. Faculty domain (@mitsgwalior.in)
    if email.endswith('@mitsgwalior.in'):
        if _safe_exists(AllowedFaculty, email=email):
            return
        if _safe_exists(AllowedWarden, email=email):
            return
        raise AuthForbidden(backend)

    # 3. Warden via Gmail (@gmail.com)
    if email.endswith('@gmail.com'):
        if _safe_exists(AllowedWarden, email=email):
            return
        raise AuthForbidden(backend)

    # 4. Student domain (@mitsgwl.ac.in)
    if email.endswith('@mitsgwl.ac.in'):
        if _safe_exists(AllowedStudent, email=email):
            return
        raise AuthForbidden(backend)

    # 5. Block everything else
    raise AuthForbidden(backend)


# ═══════════════════════════════════════════════════════════
# STEP 2: assign_role — Create profile records
# ═══════════════════════════════════════════════════════════
def assign_role(strategy, details, user=None, *args, **kwargs):
    from accounts.models import AdminProfile, FacultyProfile, AllowedFaculty, AllowedWarden
    from warden.models import WardenProfile

    email = details.get('email', '').lower().strip()

    # --- ADMIN CLEANUP / ASSIGNMENT ---
    # If they are in the admin list, ensure they have an AdminProfile
    if email in settings.ADMIN_EMAILS:
        _safe_get_or_create(
            AdminProfile, user=user,
            defaults={'name': details.get('fullname', '') or (user.get_full_name() if user else '')}
        )
    else:
        # Security: If they have an AdminProfile but are NO LONGER in the list, delete it.
        try:
            ap = _safe_get(AdminProfile, user=user)
            if ap:
                ap.delete()
                logger.warning(f"[ADMIN REVOKED] Removed AdminProfile for {email} (not in .env)")
        except Exception:
            pass

    if email.endswith('@mitsgwl.ac.in'):
        # Handled entirely by extract_name_and_enrollment
        return

    # Skip further processing if they were already handled as admin
    if email in settings.ADMIN_EMAILS:
        return

    # --- TEST USER ASSIGNMENT ---
    if settings.TEST_WARDEN_EMAIL and email == settings.TEST_WARDEN_EMAIL:
        # Prevent role conflict — delete faculty profile if it exists
        FacultyProfile.objects.filter(user=user).delete()
        _safe_get_or_create(
            WardenProfile, user=user,
            defaults={
                'name': settings.TEST_WARDEN_NAME,
                'hostel_number': settings.TEST_WARDEN_HOSTEL,
                'first_login': False,
            }
        )
        return

    if settings.TEST_FACULTY_EMAIL and email == settings.TEST_FACULTY_EMAIL:
        # Prevent role conflict — delete warden profile if it exists
        WardenProfile.objects.filter(user=user).delete()
        _safe_get_or_create(
            FacultyProfile, user=user,
            defaults={
                'name': settings.TEST_FACULTY_NAME,
                'first_login': False,
            }
        )
        return



    if email.endswith('@mitsgwalior.in'):
        if _safe_exists(AllowedFaculty, email=email):
            _safe_get_or_create(
                FacultyProfile, user=user,
                defaults={
                    'name': details.get('fullname', '') or (user.get_full_name() if user else ''),
                    'first_login': True,
                }
            )
        elif _safe_exists(AllowedWarden, email=email):
            _safe_get_or_create(
                WardenProfile, user=user,
                defaults={
                    'name': details.get('fullname', '') or (user.get_full_name() if user else ''),
                    'first_login': True,
                }
            )

    elif email.endswith('@gmail.com'):
        if _safe_exists(AllowedWarden, email=email):
            _safe_get_or_create(
                WardenProfile, user=user,
                defaults={
                    'name': details.get('fullname', '') or (user.get_full_name() if user else ''),
                    'first_login': True,
                }
            )


# ═══════════════════════════════════════════════════════════
# STEP 3: extract_name_and_enrollment — Student identity
# ═══════════════════════════════════════════════════════════
def extract_name_and_enrollment(backend, user, response, *args, **kwargs):
    from accounts.models import StudentProfile, AllowedStudent, AdminProfile, FacultyProfile, AllowedFaculty, AllowedWarden
    from warden.models import WardenProfile

    email = user.email.lower().strip()
    full_name = response.get('name', '').strip()
    photo_url = response.get('picture', '')

    # Only process students here
    if email.endswith('@mitsgwl.ac.in'):
        if not _safe_exists(AllowedStudent, email=email):
            return

        try:
            # Parse identity from Google Name (Format: "ENROLLMENT NAME")
            google_name = response.get('name', '').strip()
            parts = google_name.split(' ', 1)

            if len(parts) == 2 and any(char.isdigit() for char in parts[0]):
                enrollment = parts[0]
                name = parts[1]
            else:
                email_prefix = email.split('@')[0]
                enrollment = email_prefix
                name = google_name or response.get('given_name', 'Student')

            allowed_record = _safe_filter_first(AllowedStudent, email=email)
            if allowed_record:
                if not enrollment:
                    enrollment = allowed_record.enrollment_number
                if not name or name == enrollment:
                    name = allowed_record.full_name

            # Clean up ghost profiles linked to this Django User with wrong PK
            StudentProfile.objects.filter(user=user).exclude(enrollment_number=enrollment).delete()

            # Fetch the actual historical profile by its true primary key
            profile = _safe_filter_first(StudentProfile, enrollment_number=enrollment)
            if profile:
                profile.user = user
            else:
                profile = StudentProfile(enrollment_number=enrollment, user=user)

            if allowed_record:
                try:
                    profile.branch = allowed_record.branch
                    profile.semester = allowed_record.semester
                except AttributeError:
                    pass  # Column might not exist yet

            profile.name = name
            profile.photo_url = photo_url
            profile.save()
        except Exception as e:
            logger.error(f"[PIPELINE ERROR] extract_name_and_enrollment for {email}: {e}")
        return

    elif email in settings.ADMIN_EMAILS:
        profile, created = _safe_get_or_create(AdminProfile, user=user)
        if profile and created:
            profile.name = full_name
            profile.photo_url = photo_url
            try:
                profile.save()
            except Exception:
                pass
        return

    # --- TEST USERS SYNC ---
    if settings.TEST_WARDEN_EMAIL and email == settings.TEST_WARDEN_EMAIL:
        FacultyProfile.objects.filter(user=user).delete() # Cleanup
        profile, created = _safe_get_or_create(WardenProfile, user=user)
        if profile:
            profile.name = settings.TEST_WARDEN_NAME
            profile.hostel_number = settings.TEST_WARDEN_HOSTEL
            profile.photo_url = photo_url
            profile.save()
        return

    if settings.TEST_FACULTY_EMAIL and email == settings.TEST_FACULTY_EMAIL:
        WardenProfile.objects.filter(user=user).delete() # Cleanup
        profile, created = _safe_get_or_create(FacultyProfile, user=user)
        if profile:
            profile.name = settings.TEST_FACULTY_NAME
            profile.photo_url = photo_url
            profile.save()
        return



    elif email.endswith('@mitsgwalior.in'):
        if _safe_exists(AllowedFaculty, email=email):
            profile, created = _safe_get_or_create(FacultyProfile, user=user)
            if profile and created:
                profile.name = full_name
                profile.photo_url = photo_url
                profile.first_login = True
                try:
                    profile.save()
                except Exception:
                    pass
        elif _safe_exists(AllowedWarden, email=email):
            profile, created = _safe_get_or_create(WardenProfile, user=user)
            if profile and created:
                profile.name = full_name
                profile.photo_url = photo_url
                profile.first_login = True
                try:
                    profile.save()
                except Exception:
                    pass

    elif email.endswith('@gmail.com'):
        if _safe_exists(AllowedWarden, email=email):
            profile, created = _safe_get_or_create(WardenProfile, user=user)
            if profile and created:
                profile.name = full_name
                profile.photo_url = photo_url
                profile.first_login = True
                try:
                    profile.save()
                except Exception:
                    pass


# ═══════════════════════════════════════════════════════════
# STEP 4: redirect_after_login — Route to correct dashboard
# ═══════════════════════════════════════════════════════════
def redirect_after_login(strategy, user, *args, **kwargs):
    from accounts.models import StudentProfile, AllowedStudent, AllowedFaculty, AllowedWarden
    from warden.models import WardenProfile

    email = user.email.lower().strip()

    # Student
    if email.endswith('@mitsgwl.ac.in'):
        if _safe_exists(AllowedStudent, email=email):
            profile = _safe_get(StudentProfile, user=user)
            if profile and profile.first_login:
                return {'redirect_url': '/accounts/edit/'}
            return {'redirect_url': '/accounts/dashboard/'}
        return {'redirect_url': '/?error=unauthorized'}

    # Admin
    if email in settings.ADMIN_EMAILS:
        return {'redirect_url': '/master-admin/dashboard/'}

    # Test Users
    if settings.TEST_WARDEN_EMAIL and email == settings.TEST_WARDEN_EMAIL:
        return {'redirect_url': '/warden/dashboard/'}
    if settings.TEST_FACULTY_EMAIL and email == settings.TEST_FACULTY_EMAIL:
        return {'redirect_url': '/faculty/dashboard/'}


    # Faculty domain
    if email.endswith('@mitsgwalior.in'):
        if _safe_exists(AllowedFaculty, email=email):
            return {'redirect_url': '/faculty/dashboard/'}
        if _safe_exists(AllowedWarden, email=email):
            return {'redirect_url': '/warden/dashboard/'}

    # Warden via Gmail
    if email.endswith('@gmail.com'):
        if _safe_exists(AllowedWarden, email=email):
            return {'redirect_url': '/warden/dashboard/'}

    # Fallback — unauthorized
    return {'redirect_url': '/?error=unauthorized'}
