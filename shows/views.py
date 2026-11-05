# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Genre, Show

SHOWS_PER_PAGE = 12
RECENT_SHOW_COUNT = 6


def home(request):
    context = {
        'show_total': Show.objects.count(),
        'recent_shows': Show.objects.select_related('genre').order_by('-created_at', '-pk')[:RECENT_SHOW_COUNT],
    }
    return render(request, 'shows/home.html', context)


def show_list(request):
    query = request.GET.get('q', '').strip()
    selected_genre = request.GET.get('genre', '')

    shows = Show.objects.select_related('genre')
    if query:
        shows = shows.filter(Q(title__icontains=query) | Q(network__icontains=query))
    if selected_genre:
        shows = shows.filter(genre__name=selected_genre)

    context = {
        # get_page falls back to a valid page if ?page= is missing or out of range.
        'page_obj': Paginator(shows, SHOWS_PER_PAGE).get_page(request.GET.get('page')),
        'genres': Genre.objects.all(),
        'query': query,
        'selected_genre': selected_genre,
    }
    return render(request, 'shows/show_list.html', context)


def show_detail(request, pk):
    show = get_object_or_404(Show.objects.select_related('genre'), pk=pk)
    return render(request, 'shows/show_detail.html', {'show': show})
