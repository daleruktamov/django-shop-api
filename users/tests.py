from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class RegistrationTests(APITestCase):
    url = "/api/auth/register/"

    def test_registration_returns_token_pair(self):
        response = self.client.post(
            self.url,
            {
                "username": "newbuyer",
                "email": "newbuyer@example.com",
                "password": "Sup3rSecret!42",
                "password2": "Sup3rSecret!42",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], User.Role.CUSTOMER)

    def test_passwords_must_match(self):
        response = self.client.post(
            self.url,
            {
                "username": "newbuyer",
                "email": "newbuyer@example.com",
                "password": "Sup3rSecret!42",
                "password2": "another-one",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="newbuyer").exists())

    def test_email_must_be_unique(self):
        User.objects.create_user(
            username="first", email="taken@example.com", password="Sup3rSecret!42"
        )

        response = self.client.post(
            self.url,
            {
                "username": "second",
                "email": "taken@example.com",
                "password": "Sup3rSecret!42",
                "password2": "Sup3rSecret!42",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)


class LoginTests(APITestCase):
    url = "/api/auth/login/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer", email="buyer@example.com", password="Sup3rSecret!42"
        )

    def test_login_by_username(self):
        response = self.client.post(
            self.url, {"login": "buyer", "password": "Sup3rSecret!42"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_by_email(self):
        response = self.client.post(
            self.url,
            {"login": "buyer@example.com", "password": "Sup3rSecret!42"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.data)

    def test_wrong_password_is_rejected(self):
        response = self.client.post(
            self.url, {"login": "buyer", "password": "wrong"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_token_gives_new_access(self):
        tokens = self.client.post(
            self.url, {"login": "buyer", "password": "Sup3rSecret!42"}, format="json"
        ).data

        response = self.client.post(
            "/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


class ProfileTests(APITestCase):
    url = "/api/auth/me/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer", email="buyer@example.com", password="Sup3rSecret!42"
        )

    def test_guest_cannot_open_profile(self):
        self.assertEqual(
            self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_user_can_edit_own_profile(self):
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            self.url,
            {"phone": "+998901112233", "address": "Ташкент, Юнусабад"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+998901112233")

    def test_role_cannot_be_raised_through_profile(self):
        self.client.force_authenticate(self.user)

        self.client.patch(self.url, {"role": User.Role.ADMIN}, format="json")

        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.CUSTOMER)


class UserListTests(APITestCase):
    url = "/api/auth/users/"

    def setUp(self):
        self.customer = User.objects.create_user(
            username="buyer", email="buyer@example.com", password="Sup3rSecret!42"
        )
        self.admin = User.objects.create_superuser(
            username="boss", email="boss@example.com", password="Sup3rSecret!42"
        )

    def test_customer_cannot_list_users(self):
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_users(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
