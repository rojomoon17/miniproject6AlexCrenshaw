# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shows.urls')),
]
