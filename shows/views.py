# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import WatchEntryForm
from .models import Genre, Show, WatchEntry

SHOWS_PER_PAGE = 12
RECENT_SHOW_COUNT = 6
CONTINUE_WATCHING_COUNT = 3


def home(request):
    context = {
        'show_total': Show.objects.count(),
        'recent_shows': Show.objects.select_related('genre').order_by('-created_at', '-pk')[:RECENT_SHOW_COUNT],
    }
    if request.user.is_authenticated:
        context['continue_watching'] = (
            request.user.watch_entries
            .filter(status=WatchEntry.Status.WATCHING)
            .select_related('show')[:CONTINUE_WATCHING_COUNT]
        )
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
    entry = None
    if request.user.is_authenticated:
        entry = request.user.watch_entries.filter(show=show).first()
    return render(request, 'shows/show_detail.html', {'show': show, 'entry': entry})


@login_required
def watchlist(request):
    entries = list(request.user.watch_entries.select_related('show', 'show__genre'))
    groups = []
    for value, label in WatchEntry.Status.choices:
        group_entries = [entry for entry in entries if entry.status == value]
        if group_entries:
            groups.append({'label': label, 'entries': group_entries})

    context = {
        'groups': groups,
        'show_total': len(entries),
        'episode_total': sum(entry.episodes_watched for entry in entries),
    }
    return render(request, 'shows/watchlist.html', context)


@login_required
def entry_add(request, show_pk):
    show = get_object_or_404(Show, pk=show_pk)

    existing = request.user.watch_entries.filter(show=show).first()
    if existing:
        messages.info(request, f'{show.title} is already on your watchlist.')
        return redirect('shows:entry_edit', pk=existing.pk)

    entry = WatchEntry(user=request.user, show=show)
    if request.method == 'POST':
        form = WatchEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, f'Added {show.title} to your watchlist.')
            return redirect('shows:watchlist')
    else:
        form = WatchEntryForm(instance=entry)

    return render(request, 'shows/entry_form.html', {'form': form, 'show': show, 'is_new': True})


@login_required
def entry_edit(request, pk):
    # Filtering by user makes another user's entry a 404, so its existence isn't revealed.
    entry = get_object_or_404(WatchEntry.objects.select_related('show'), pk=pk, user=request.user)

    if request.method == 'POST':
        form = WatchEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, f'Updated {entry.show.title}.')
            return redirect('shows:watchlist')
    else:
        form = WatchEntryForm(instance=entry)

    return render(request, 'shows/entry_form.html', {'form': form, 'show': entry.show, 'is_new': False})


@login_required
@require_POST
def entry_delete(request, pk):
    entry = get_object_or_404(WatchEntry.objects.select_related('show'), pk=pk, user=request.user)
    title = entry.show.title
    entry.delete()
    messages.success(request, f'Removed {title} from your watchlist.')
    return redirect('shows:watchlist')
