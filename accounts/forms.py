# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

import hashlib

from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.cache import cache
from django.core.exceptions import ValidationError

from shows.forms import BootstrapFormMixin

LOGIN_MAX_FAILURES = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60


class LoginThrottleMixin:
    """Blocks a username from one IP address for 15 minutes after 5 failed logins in a row."""

    def clean(self):
        key = self.throttle_key()
        if cache.get(key, 0) >= LOGIN_MAX_FAILURES:
            raise ValidationError('Too many failed login attempts. Try again in 15 minutes.', code='throttled')
        try:
            cleaned_data = super().clean()
        except ValidationError:
            # add only sets the timeout on the first failure, so more failures can't extend the lockout.
            cache.add(key, 0, LOGIN_LOCKOUT_SECONDS)
            cache.incr(key)
            raise
        cache.delete(key)
        return cleaned_data

    def throttle_key(self):
        username = self.cleaned_data.get('username', '').lower()
        address = self.request.META.get('REMOTE_ADDR', '') if self.request else ''
        # Hashed because usernames can contain characters that aren't valid in a cache key.
        return 'login-failures-' + hashlib.sha256(f'{address}|{username}'.encode()).hexdigest()


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    pass


class LoginForm(LoginThrottleMixin, BootstrapFormMixin, AuthenticationForm):
    pass


class AdminLoginForm(LoginThrottleMixin, AdminAuthenticationForm):
    pass
