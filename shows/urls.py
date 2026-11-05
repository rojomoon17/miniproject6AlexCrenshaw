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
    path('shows/<int:show_pk>/track/', views.entry_add, name='entry_add'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('watchlist/<int:pk>/edit/', views.entry_edit, name='entry_edit'),
    path('watchlist/<int:pk>/remove/', views.entry_delete, name='entry_delete'),
]
