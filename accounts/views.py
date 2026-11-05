# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account is ready.')
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})
