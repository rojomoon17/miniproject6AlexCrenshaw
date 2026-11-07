# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .forms import LOGIN_MAX_FAILURES

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


class LoginThrottleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_superuser('alice', password=PASSWORD)

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def fail_logins(self, url=None, count=LOGIN_MAX_FAILURES, username='alice'):
        for _ in range(count):
            self.client.post(url or reverse('login'), {'username': username, 'password': 'wrong'})

    def test_correct_password_is_refused_after_too_many_failures(self):
        self.fail_logins()
        response = self.client.post(reverse('login'), {'username': 'alice', 'password': PASSWORD})
        self.assertContains(response, 'Too many failed login attempts')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_usernames_differing_only_by_case_share_a_limit(self):
        self.fail_logins(username='ALICE')
        response = self.client.post(reverse('login'), {'username': 'alice', 'password': PASSWORD})
        self.assertContains(response, 'Too many failed login attempts')

    def test_failures_below_the_limit_still_allow_login(self):
        self.fail_logins(count=LOGIN_MAX_FAILURES - 1)
        self.client.post(reverse('login'), {'username': 'alice', 'password': PASSWORD})
        self.assertIn('_auth_user_id', self.client.session)

    def test_successful_login_resets_the_count(self):
        self.fail_logins(count=LOGIN_MAX_FAILURES - 1)
        self.client.post(reverse('login'), {'username': 'alice', 'password': PASSWORD})
        self.client.post(reverse('logout'))
        self.fail_logins(count=LOGIN_MAX_FAILURES - 1)
        self.client.post(reverse('login'), {'username': 'alice', 'password': PASSWORD})
        self.assertIn('_auth_user_id', self.client.session)

    def test_other_usernames_and_addresses_are_not_blocked(self):
        get_user_model().objects.create_user('bob', password=PASSWORD)
        self.fail_logins()
        self.client.post(reverse('login'), {'username': 'bob', 'password': PASSWORD})
        self.assertIn('_auth_user_id', self.client.session)
        self.client.post(reverse('logout'))
        self.client.post(reverse('login'), {'username': 'alice', 'password': PASSWORD}, REMOTE_ADDR='10.0.0.9')
        self.assertIn('_auth_user_id', self.client.session)

    def test_admin_login_is_throttled_too(self):
        url = reverse('admin:login')
        self.fail_logins(url=url)
        response = self.client.post(url, {'username': 'alice', 'password': PASSWORD})
        self.assertContains(response, 'Too many failed login attempts')
        self.assertNotIn('_auth_user_id', self.client.session)
