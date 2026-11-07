# INF601 - Advanced Programming in Python
# Alex Crenshaw
# Mini Project 6

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .forms import MAX_PENDING_REQUESTS_PER_USER
from .models import Genre, Show, ShowRequest, WatchEntry


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


class ShowRequestTests(ShowTestCase):
    def setUp(self):
        self.list_url = reverse('shows:request_list')
        self.add_url = reverse('shows:request_add')

    def post_request(self, **overrides):
        self.client.force_login(self.alice)
        data = {'title': 'New Show', 'network': 'Netflix', 'note': 'Please add it'}
        data.update(overrides)
        return self.client.post(self.add_url, data)

    def test_list_is_public_and_shows_the_request(self):
        ShowRequest.objects.create(title='New Show', note='Please add it', requested_by=self.alice)
        response = self.client.get(self.list_url)
        self.assertContains(response, 'New Show')
        self.assertContains(response, 'Please add it')
        self.assertContains(response, 'alice')

    def test_add_requires_login(self):
        self.assertRedirects(self.client.get(self.add_url), f"{reverse('login')}?next={self.add_url}")
        self.client.post(self.add_url, {'title': 'New Show'})
        self.assertFalse(ShowRequest.objects.exists())

    def test_add_saves_a_pending_request_for_the_logged_in_user(self):
        self.assertRedirects(self.post_request(), self.list_url)
        show_request = ShowRequest.objects.get()
        self.assertEqual(
            (show_request.title, show_request.network, show_request.requested_by, show_request.status),
            ('New Show', 'Netflix', self.alice, 'pending'),
        )

    def test_form_ignores_posted_status_and_requester(self):
        self.post_request(status='added', requested_by=self.bob.pk)
        show_request = ShowRequest.objects.get()
        self.assertEqual((show_request.status, show_request.requested_by), ('pending', self.alice))

    def test_rejects_a_blank_title(self):
        self.assertIn('title', self.post_request(title='   ').context['form'].errors)
        self.assertFalse(ShowRequest.objects.exists())

    def test_rejects_a_show_already_in_the_catalog(self):
        self.assertIn('title', self.post_request(title='test crime show').context['form'].errors)
        self.assertFalse(ShowRequest.objects.exists())

    def test_rejects_a_title_with_a_pending_request(self):
        ShowRequest.objects.create(title='New Show', requested_by=self.bob)
        self.assertIn('title', self.post_request(title='new show').context['form'].errors)
        self.assertEqual(ShowRequest.objects.count(), 1)

    def test_a_declined_title_can_be_requested_again(self):
        ShowRequest.objects.create(title='New Show', requested_by=self.bob, status='declined')
        self.assertRedirects(self.post_request(), self.list_url)
        self.assertEqual(ShowRequest.objects.count(), 2)

    def test_limits_each_users_pending_requests(self):
        for number in range(MAX_PENDING_REQUESTS_PER_USER):
            ShowRequest.objects.create(title=f'Show {number}', requested_by=self.alice)
        self.assertContains(self.post_request(), 'pending requests')
        self.assertEqual(ShowRequest.objects.count(), MAX_PENDING_REQUESTS_PER_USER)

        ShowRequest.objects.filter(title='Show 0').update(status='added')
        self.assertRedirects(self.post_request(), self.list_url)

    def test_status_filter(self):
        ShowRequest.objects.create(title='Waiting Show', requested_by=self.alice)
        ShowRequest.objects.create(title='Refused Show', requested_by=self.alice, status='declined')
        response = self.client.get(self.list_url, {'status': 'declined'})
        self.assertContains(response, 'Refused Show')
        self.assertNotContains(response, 'Waiting Show')

    def test_unknown_status_shows_everything(self):
        ShowRequest.objects.create(title='Waiting Show', requested_by=self.alice)
        response = self.client.get(self.list_url, {'status': 'nonsense'})
        self.assertContains(response, 'Waiting Show')
        self.assertEqual(response.context['selected_status'], '')

    def test_user_text_is_escaped(self):
        ShowRequest.objects.create(title='<script>x</script>', note='<b>y</b>', requested_by=self.alice)
        response = self.client.get(self.list_url)
        self.assertNotContains(response, '<script>x</script>')
        self.assertNotContains(response, '<b>y</b>')

    def test_empty_search_links_to_a_prefilled_request(self):
        response = self.client.get(reverse('shows:show_list'), {'q': 'Missing Show'})
        self.assertContains(response, f'{self.add_url}?title=Missing%20Show')
        self.client.force_login(self.alice)
        response = self.client.get(self.add_url, {'title': 'Missing Show'})
        self.assertEqual(response.context['form'].initial['title'], 'Missing Show')


class SampleDataTests(TestCase):
    fixtures = ['sample_shows']

    def test_example_request_is_listed(self):
        response = self.client.get(reverse('shows:request_list'))
        self.assertContains(response, 'Lanterns (2026)')
        self.assertContains(response, 'sample_viewer')

    def test_example_user_cannot_log_in(self):
        self.assertFalse(get_user_model().objects.get(username='sample_viewer').has_usable_password())
