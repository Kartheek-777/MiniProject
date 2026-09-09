from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import StudentProfile

class Phase2AuthenticationAndDatabaseTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.dashboard_url = reverse('dashboard_home')

    def test_complete_user_lifecycle_flow(self):
        # 1. New User Registration
        registration_data = {
            'first_name': 'Rahul',
            'last_name': 'Sharma',
            'username': 'rahul_sde',
            'email': 'rahul@engineering.edu',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'college': 'Indian Institute of Technology',
            'degree': 'B.Tech',
            'branch': 'Computer Science & Engineering',
            'graduation_year': 2026,
            'cgpa': '8.90',
            'target_role': 'Software Development Engineer',
            'phone_number': '+919876543210',
        }
        reg_response = self.client.post(self.register_url, registration_data)
        self.assertEqual(reg_response.status_code, 302)  # Redirects to login on success
        
        # Verify User and StudentProfile created in DB
        user = User.objects.get(username='rahul_sde')
        self.assertEqual(user.first_name, 'Rahul')
        self.assertEqual(user.email, 'rahul@engineering.edu')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.college, 'Indian Institute of Technology')
        self.assertEqual(user.profile.target_role, 'Software Development Engineer')
        self.assertGreater(user.profile.completion_percentage, 50)

        # 2. Login with registered credentials
        login_data = {
            'username': 'rahul_sde',
            'password': 'SecurePass123!',
        }
        login_response = self.client.post(self.login_url, login_data)
        self.assertEqual(login_response.status_code, 302)
        self.assertRedirects(login_response, self.dashboard_url)

        # 3. Access Protected Dashboard
        dash_response = self.client.get(self.dashboard_url)
        self.assertEqual(dash_response.status_code, 200)
        self.assertContains(dash_response, "Rahul Sharma")
        self.assertContains(dash_response, "Software Development Engineer")
        self.assertContains(dash_response, "Indian Institute of Technology")

        # 4. Logout
        logout_response = self.client.get(self.logout_url)
        self.assertEqual(logout_response.status_code, 302)

        # 5. Attempt Dashboard Access Post-Logout (Verify Protection)
        protected_attempt = self.client.get(self.dashboard_url)
        self.assertEqual(protected_attempt.status_code, 302)
        self.assertIn(self.login_url, protected_attempt.url)

    def test_invalid_registration_data(self):
        # Mismatched passwords and duplicate username
        User.objects.create_user(username='existing_student', password='Pass12345!')
        invalid_data = {
            'first_name': 'Test',
            'last_name': 'Student',
            'username': 'existing_student',
            'email': 'invalid-email',
            'password1': 'Password123!',
            'password2': 'DifferentPassword123!',
        }
        response = self.client.post(self.register_url, invalid_data)
        self.assertEqual(response.status_code, 200)  # Form redisplayed with errors
        self.assertContains(response, "This username is already taken")
        self.assertContains(response, "Passwords do not match")

    def test_invalid_login_credentials(self):
        User.objects.create_user(username='valid_student', password='CorrectPassword123!')
        
        # Wrong password
        bad_login = self.client.post(self.login_url, {'username': 'valid_student', 'password': 'WrongPassword!'})
        self.assertEqual(bad_login.status_code, 200)
        self.assertContains(bad_login, "Invalid username or password.")

    def test_google_login_direct_account_chooser(self):
        # Clicking Google Sign-Up/Sign-In opens the Google Account Chooser screen
        response = self.client.get(reverse('google_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose an account")
        self.assertContains(response, "to continue to")
        self.assertContains(response, "kartheek777lagisetti@gmail.com")

    @override_settings(DEBUG=True)
    def test_google_demo_login_flow(self):
        # Test 1-click Google Demo Sandbox Sign-In
        response = self.client.get(reverse('google_demo'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.dashboard_url)

        # Verify Google user and profile were created
        user = User.objects.get(email="alex.rivera.google@example.com")
        self.assertEqual(user.first_name, "Alex")
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.college, "Stanford Institute of Technology")

    def test_google_login_redirect_when_configured(self):
        # When Google Client ID and Secret are configured, redirects to accounts.google.com
        with self.settings(GOOGLE_CLIENT_ID="mock_client_id.apps.googleusercontent.com", GOOGLE_CLIENT_SECRET="mock_secret"):
            response = self.client.get(reverse('google_login'))
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith("https://accounts.google.com/o/oauth2/v2/auth"))
            self.assertIn("client_id=mock_client_id", response.url)
