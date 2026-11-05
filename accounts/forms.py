# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from shows.forms import BootstrapFormMixin


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    pass


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass
