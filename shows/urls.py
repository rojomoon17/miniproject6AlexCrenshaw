# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django.urls import path

from . import views

app_name = 'shows'

urlpatterns = [
    path('', views.home, name='home'),
    path('shows/', views.show_list, name='show_list'),
    path('shows/<int:pk>/', views.show_detail, name='show_detail'),
]
