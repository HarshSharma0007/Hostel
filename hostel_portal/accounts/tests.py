# python manage.py test accounts
from accounts.models import AllowedStudent
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from accounts.pipeline import assign_role
from django.test import Client


class AllowedStudentModelTest(TestCase):
    def test_allowed_student_creation(self):
        student = AllowedStudent.objects.create(email='23am10ha27@mitsgwl.ac.in')
        self.assertEqual(student.email, '23am10ha27@mitsgwl.ac.in')


class LoginFlowTest(TestCase):
    def test_login_redirect(self):
        client = Client()
        response = client.get('/accounts/login/google-oauth2/')
        self.assertEqual(response.status_code, 302)


class AssignRoleTest(TestCase):
    def test_login_persists(self):
        user = User.objects.create_user(username='testuser', email='test@mitsgwl.ac.in')
        user.backend = 'django.contrib.auth.backends.ModelBackend'

        factory = RequestFactory()
        request = factory.get('/')

        # Attach session
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        # ✅ Attach user manually (since middleware isn't run)
        request.user = user

        assign_role(backend=None, user=user, request=request)

        self.assertTrue(request.user.is_authenticated)
