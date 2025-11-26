from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


User = get_user_model()


class TestUserRegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        """
        Test that a new user can register successfully.
        URL: /api/auth/register/
        """
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongPass123",
            "password2": "StrongPass123"  # required by serializer
        }
        response = self.client.post("/api/auth/register/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.check_password("StrongPass123"))

class TestUserLogin(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = "/api/auth/login/"  # Make sure this matches your login endpoint
        # Create a test user for login
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPass123",
            first_name="Test",
            last_name="User"
        )

    def test_login_success(self):
        """
        Test that a user can login with correct credentials and receive JWT tokens
        """
        data = {
            "username": "testuser",
            "password": "StrongPass123"
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self):
        """
        Test login fails with wrong password
        """
        data = {
            "username": "testuser",
            "password": "WrongPass123"
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_login_nonexistent_user(self):
        """
        Test login fails for a non-existent user
        """
        data = {
            "username": "nouser",
            "password": "StrongPass123"
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

class TestUserLogout(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.logout_url = "/api/auth/logout/"
        self.login_url = "/api/auth/login/"
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPass123",
            first_name="Test",
            last_name="User"
        )

    def test_logout_success(self):
        """
        Test that a logged-in user can logout successfully and the refresh token is blacklisted
        """
        # 1. Login to get JWT tokens
        login_data = {"username": "testuser", "password": "StrongPass123"}
        login_response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(login_response.status_code, 200)

        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        # 2. Authenticate client with access token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 3. Call logout endpoint
        response = self.client.post(self.logout_url, {"refresh": refresh_token}, format="json")
        self.assertEqual(response.status_code, 205)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "User logged out successfully.")

        # 4. Optional: Ensure refresh token is blacklisted
        with self.assertRaises(TokenError):
            refresh = RefreshToken(refresh_token)
            refresh.blacklist()




# Create your tests here.
