# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Show(models.Model):
    """A TV show in the shared catalog, managed by staff through the admin."""

    title = models.CharField(max_length=200)
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT, related_name='shows')
    network = models.CharField(max_length=100)
    premiere_year = models.PositiveSmallIntegerField(validators=[MinValueValidator(1928)])
    season_count = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    episode_count = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        constraints = [
            models.UniqueConstraint(fields=['title', 'premiere_year'], name='unique_show_title_year'),
        ]

    def __str__(self):
        return f'{self.title} ({self.premiere_year})'

    def get_absolute_url(self):
        return reverse('shows:show_detail', args=[self.pk])


class WatchEntry(models.Model):
    """One user's progress on one show."""

    class Status(models.TextChoices):
        WATCHING = 'watching', 'Watching'
        PLANNED = 'planned', 'Plan to watch'
        ON_HOLD = 'on_hold', 'On hold'
        COMPLETED = 'completed', 'Completed'
        DROPPED = 'dropped', 'Dropped'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watch_entries')
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='watch_entries')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    episodes_watched = models.PositiveIntegerField(default=0)
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='Optional, from 1 to 10.',
    )
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = 'watch entries'
        constraints = [
            models.UniqueConstraint(fields=['user', 'show'], name='unique_watch_entry_per_user'),
        ]

    def __str__(self):
        return f'{self.user} - {self.show.title}'

    def clean(self):
        # Runs for both the site form and the admin, so the rules live in one place.
        if self.show_id is None or self.episodes_watched is None:
            return
        if self.episodes_watched > self.show.episode_count:
            raise ValidationError(
                {'episodes_watched': f'This show only has {self.show.episode_count} episodes.'}
            )
        if self.status == self.Status.COMPLETED:
            self.episodes_watched = self.show.episode_count

    @property
    def progress_percent(self):
        # Capped because staff can lower a show's episode count after progress is recorded.
        return min(round(self.episodes_watched / self.show.episode_count * 100), 100)
