# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Genre, Show, WatchEntry


class ShowTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.alice = User.objects.create_user('alice', password='test-pass-123')
        cls.bob = User.objects.create_user('bob', password='test-pass-123')
        cls.crime = Genre.objects.create(name='Crime')
        cls.comedy = Genre.objects.create(name='Comedy')
        cls.show = Show.objects.create(
            title='Test Crime Show', genre=cls.crime, network='HBO', premiere_year=2002, episode_count=10,
        )
        cls.other_show = Show.objects.create(
            title='Test Comedy Show', genre=cls.comedy, network='NBC', premiere_year=2005, episode_count=20,
        )


class PublicPageTests(ShowTestCase):
    def test_public_pages_load_while_logged_out(self):
        urls = [reverse('shows:home'), reverse('shows:show_list'), self.show.get_absolute_url()]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_search_matches_title(self):
        response = self.client.get(reverse('shows:show_list'), {'q': 'crime'})
        self.assertContains(response, 'Test Crime Show')
        self.assertNotContains(response, 'Test Comedy Show')

    def test_genre_filter(self):
        response = self.client.get(reverse('shows:show_list'), {'genre': 'Comedy'})
        self.assertContains(response, 'Test Comedy Show')
        self.assertNotContains(response, 'Test Crime Show')

    def test_unknown_show_is_404(self):
        self.assertEqual(self.client.get(reverse('shows:show_detail', args=[99999])).status_code, 404)


class OrganizationTests(ShowTestCase):
    def test_home_has_a_shelf_for_each_genre_with_shows(self):
        Genre.objects.create(name='Empty Genre')
        response = self.client.get(reverse('shows:home'))
        self.assertEqual([genre.name for genre in response.context['shelves']], ['Comedy', 'Crime'])
        self.assertContains(response, 'Test Crime Show')

    def test_detail_suggests_other_shows_in_the_genre(self):
        same_genre = Show.objects.create(
            title='Another Crime Show', genre=self.crime, network='AMC', premiere_year=2008,
        )
        response = self.client.get(self.show.get_absolute_url())
        self.assertEqual(list(response.context['related_shows']), [same_genre])

    def test_genre_chips_keep_the_search_and_all_clears_the_genre(self):
        response = self.client.get(reverse('shows:show_list'), {'q': 'test', 'genre': 'Crime', 'page': 1})
        self.assertContains(response, 'href="?q=test"')
        self.assertContains(response, 'href="?q=test&amp;genre=Comedy"')

    def test_watchlist_totals(self):
        WatchEntry.objects.create(user=self.alice, show=self.show, status='completed', episodes_watched=10, rating=9)
        WatchEntry.objects.create(user=self.alice, show=self.other_show, episodes_watched=5, rating=6)
        self.client.force_login(self.alice)
        context = self.client.get(reverse('shows:watchlist')).context
        self.assertEqual(
            (context['show_total'], context['episode_total'], context['completed_total'], context['average_rating']),
            (2, 15, 1, 7.5),
        )
        self.assertEqual([group['value'] for group in context['groups']], ['planned', 'completed'])

    def test_average_rating_is_empty_without_ratings(self):
        WatchEntry.objects.create(user=self.alice, show=self.show)
        self.client.force_login(self.alice)
        self.assertIsNone(self.client.get(reverse('shows:watchlist')).context['average_rating'])


class LoginRequiredTests(ShowTestCase):
    def test_private_pages_redirect_to_login(self):
        entry = WatchEntry.objects.create(user=self.alice, show=self.show)
        urls = [
            reverse('shows:watchlist'),
            reverse('shows:entry_add', args=[self.show.pk]),
            reverse('shows:entry_edit', args=[entry.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_logged_out_delete_does_not_remove_entry(self):
        entry = WatchEntry.objects.create(user=self.alice, show=self.show)
        self.client.post(reverse('shows:entry_delete', args=[entry.pk]))
        self.assertTrue(WatchEntry.objects.filter(pk=entry.pk).exists())


class OwnershipTests(ShowTestCase):
    def setUp(self):
        self.entry = WatchEntry.objects.create(user=self.alice, show=self.show, episodes_watched=3)
        self.client.force_login(self.bob)

    def test_cannot_view_another_users_entry(self):
        self.assertEqual(self.client.get(reverse('shows:entry_edit', args=[self.entry.pk])).status_code, 404)

    def test_cannot_edit_another_users_entry(self):
        response = self.client.post(
            reverse('shows:entry_edit', args=[self.entry.pk]),
            {'status': 'dropped', 'episodes_watched': 0},
        )
        self.assertEqual(response.status_code, 404)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.episodes_watched, 3)

    def test_cannot_delete_another_users_entry(self):
        response = self.client.post(reverse('shows:entry_delete', args=[self.entry.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(WatchEntry.objects.filter(pk=self.entry.pk).exists())

    def test_watchlist_only_shows_own_entries(self):
        self.assertNotContains(self.client.get(reverse('shows:watchlist')), self.show.title)


class WatchEntryFormTests(ShowTestCase):
    def setUp(self):
        self.client.force_login(self.alice)
        self.add_url = reverse('shows:entry_add', args=[self.show.pk])

    def post_add(self, **overrides):
        data = {'status': 'watching', 'episodes_watched': 2, 'rating': '', 'notes': ''}
        data.update(overrides)
        return self.client.post(self.add_url, data)

    def test_add_entry(self):
        self.assertRedirects(self.post_add(rating=8, notes='Great'), reverse('shows:watchlist'))
        entry = WatchEntry.objects.get(user=self.alice, show=self.show)
        self.assertEqual((entry.episodes_watched, entry.rating, entry.notes), (2, 8, 'Great'))

    def test_rejects_more_episodes_than_the_show_has(self):
        response = self.post_add(episodes_watched=11)
        self.assertEqual(response.status_code, 200)
        self.assertIn('episodes_watched', response.context['form'].errors)
        self.assertFalse(WatchEntry.objects.exists())

    def test_rejects_ratings_outside_1_to_10(self):
        for rating in [0, 11]:
            with self.subTest(rating=rating):
                response = self.post_add(rating=rating)
                self.assertIn('rating', response.context['form'].errors)
        self.assertFalse(WatchEntry.objects.exists())

    def test_completed_marks_every_episode_watched(self):
        self.post_add(status='completed', episodes_watched=2)
        self.assertEqual(WatchEntry.objects.get().episodes_watched, 10)

    def test_adding_a_tracked_show_redirects_to_edit(self):
        entry = WatchEntry.objects.create(user=self.alice, show=self.show)
        self.assertRedirects(self.post_add(), reverse('shows:entry_edit', args=[entry.pk]))
        self.assertEqual(WatchEntry.objects.count(), 1)

    def test_database_rejects_duplicate_entries(self):
        WatchEntry.objects.create(user=self.alice, show=self.show)
        with self.assertRaises(IntegrityError), transaction.atomic():
            WatchEntry.objects.create(user=self.alice, show=self.show)

    def test_delete_requires_post(self):
        entry = WatchEntry.objects.create(user=self.alice, show=self.show)
        self.assertEqual(self.client.get(reverse('shows:entry_delete', args=[entry.pk])).status_code, 405)

    def test_delete_removes_entry(self):
        entry = WatchEntry.objects.create(user=self.alice, show=self.show)
        self.assertRedirects(
            self.client.post(reverse('shows:entry_delete', args=[entry.pk])),
            reverse('shows:watchlist'),
        )
        self.assertFalse(WatchEntry.objects.exists())


class ProgressTests(ShowTestCase):
    def test_progress_percent(self):
        entry = WatchEntry(user=self.alice, show=self.show, episodes_watched=5)
        self.assertEqual(entry.progress_percent, 50)

    def test_progress_is_capped_if_episode_count_is_lowered(self):
        entry = WatchEntry(user=self.alice, show=self.show, episodes_watched=15)
        self.assertEqual(entry.progress_percent, 100)
