from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status



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




# Create your tests here.
