# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

PASSWORD = 'Tr4cker-pass-77'


class RegisterTests(TestCase):
    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse('register'),
            {'username': 'newuser', 'password1': PASSWORD, 'password2': PASSWORD},
        )
        self.assertRedirects(response, reverse('shows:watchlist'))
        self.assertTrue(get_user_model().objects.filter(username='newuser').exists())
        self.assertEqual(self.client.get(reverse('shows:watchlist')).status_code, 200)

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse('register'),
            {'username': 'newuser', 'password1': PASSWORD, 'password2': 'different'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username='newuser').exists())


class LoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_user('alice', password=PASSWORD)

    def test_login_returns_to_the_requested_page(self):
        target = reverse('shows:watchlist')
        response = self.client.post(
            f"{reverse('login')}?next={target}",
            {'username': 'alice', 'password': PASSWORD, 'next': target},
        )
        self.assertRedirects(response, target)

    def test_wrong_password_shows_an_error(self):
        response = self.client.post(reverse('login'), {'username': 'alice', 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'alert-danger')

    def test_logout_requires_post_and_ends_the_session(self):
        self.client.login(username='alice', password=PASSWORD)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('logout')), reverse('shows:home'))
        self.assertEqual(self.client.get(reverse('shows:watchlist')).status_code, 302)
