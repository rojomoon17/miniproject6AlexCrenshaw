# TV Show Tracker

INF601 - Advanced Programming in Python | Alex Crenshaw | Mini Project 6

A Django web app for keeping track of TV shows. Anyone can browse a catalog of shows. Registered users
build a personal watchlist, recording each show's status, how many episodes they've watched, a rating
and notes. Staff manage the catalog through the Django admin.

## Features

- A dark theme with red accents, built on Bootstrap's dark mode
- Poster-style tiles for every show, with a shelf per genre on the home page
- Searchable catalog with genre filter chips and pagination
- Register, log in and log out
- A private watchlist with a tab for each status (Watching, Plan to watch, On hold, Completed, Dropped),
  progress bars, and totals including your average rating
- Show pages that suggest other shows in the same genre
- A form to add or update a show's status, progress, rating and notes, checked on the server
- A Bootstrap modal to confirm removing a show from your watchlist
- A form for logged-in users to request a show, and a public page listing every request and its status
- A customized Django admin for genres, shows, watch entries and show requests
- Users can only see and change their own watchlist entries

## Pages

| URL | Page | Access |
|---|---|---|
| `/` | Home, with your "Continue watching" list and a shelf of shows per genre | Public |
| `/shows/` | Catalog, with search and genre filter chips | Public |
| `/shows/<id>/` | Show details and your progress on that show | Public |
| `/shows/<id>/track/` | Form to add a show to your watchlist | Login required |
| `/watchlist/` | Your watchlist, grouped by status | Login required |
| `/watchlist/<id>/edit/` | Form to update your progress | Login required, owner only |
| `/requests/` | Requested shows, with a filter by status | Public |
| `/requests/new/` | Form to request a show | Login required |
| `/accounts/register/` | Create an account | Public |
| `/accounts/login/` | Log in | Public |
| `/admin/` | Django admin | Staff only |

## Requirements

- Python 3.10 or newer
- Django 5.2 (installed from `requirements.txt`)
- An internet connection when viewing the site, because Bootstrap and the fonts load from CDNs

## Installation

Clone the repository and move into it:

```bash
git clone https://github.com/rojomoon17/miniproject6AlexCrenshaw.git
cd miniproject6AlexCrenshaw
```

Create and activate a virtual environment:

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS or Linux
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

If pip reports `CERTIFICATE_VERIFY_FAILED`, antivirus HTTPS scanning may be the cause, especially with
an older pip. Recent versions of pip use the operating system's certificate store, so creating the
virtual environment with a newer Python release can fix it. Avoid `--trusted-host`, which turns
certificate checking off.

## Database initialization

The database is SQLite and isn't stored in the repository, so create it with these commands:

```bash
python manage.py makemigrations
python manage.py migrate
```

- `makemigrations` turns model changes into migration files. The migrations are already in the
  repository, so on a fresh clone it reports `No changes detected`, which is expected.
- `migrate` applies the migrations and creates `db.sqlite3`.

Create an admin account, which will ask for a username, email and password:

```bash
python manage.py createsuperuser
```

Optionally, load 17 sample shows and an example show request so the pages aren't empty. This also creates
`sample_viewer`, the example request's user, which has no password and can't log in:

```bash
python manage.py loaddata sample_shows
```

## Running the development server

```bash
python manage.py runserver
```

Then open <http://127.0.0.1:8000/>. The admin is at <http://127.0.0.1:8000/admin/>.

To try it out, register an account, open a show, choose **Add to my watchlist**, and fill in the form.
**Remove** on the watchlist opens the confirmation modal.

## Running the tests

```bash
python manage.py test
```

## Project structure

```text
miniproject6AlexCrenshaw/
├── manage.py
├── requirements.txt
├── config/                  Project settings and root URLs
├── accounts/                Registration, login and logout
│   ├── forms.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── templates/accounts/  login.html, register.html
├── shows/                   Catalog and watchlists
│   ├── admin.py             Admin configuration
│   ├── forms.py             Bootstrap form mixin and the watch entry form
│   ├── models.py            Genre, Show, WatchEntry and ShowRequest
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── fixtures/            sample_shows.json
│   ├── migrations/
│   └── templates/shows/     Page templates and reusable partials
├── static/css/              site.css and admin.css
└── templates/               base.html, site-wide partials and the admin theme override
```

## Data model

- **Genre:** a name. A genre can't be deleted while shows use it.
- **Show:** title, genre, network, premiere year, season and episode counts, and a description.
- **WatchEntry:** links one user to one show, with status, episodes watched, an optional rating from 1
  to 10, and notes. Each user can have only one entry per show.

- **ShowRequest:** a title, an optional network and note, the user who asked, and a status (Pending, Added
  or Declined). Staff set the status in the admin. The form rejects titles already in the catalog or
  already pending. A request doesn't create a show, so staff add approved shows to the catalog themselves.

`WatchEntry.clean()` holds the progress rules, so the site form and the admin both follow them:
episodes watched can't exceed the show's total, and choosing Completed marks every episode as watched.

## Configuration

With no configuration, the app runs in local development mode, with debug on and a public
development-only secret key. Don't put it online that way. These environment variables configure a
deployment:

| Variable | Purpose |
|---|---|
| `DJANGO_DEBUG` | Set to `0` to turn off debug and require HTTPS, secure cookies and HSTS |
| `DJANGO_SECRET_KEY` | The secret key. The app won't start without it when `DJANGO_DEBUG` is `0` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names the site is served from |

With debug off, `runserver` doesn't serve the CSS, and the HTTPS redirect needs an HTTPS server in front of
the app. A real deployment also needs a production web server and static file hosting, which aren't set up here.

## Security

- Django's protections for cross-site scripting, CSRF, SQL injection, clickjacking and open redirects are on,
  and no page turns them off
- Logins, including the admin's, lock for 15 minutes after 5 failed attempts in a row for the same username
  and IP address. The count is kept in memory, so it resets on restart and isn't shared between server processes
- Each user can have up to 10 pending show requests
- There's no limit on creating accounts

## AI Usage

This project was built with Claude (Opus 5.5, by Anthropic), used through Claude Code.

**Claude wrote all of the code and documentation:**

- planned the project against the assignment rubric
- designed the models, pages and URLs
- wrote every Python file, all of the templates and this README
- compiled the sample show data in `sample_shows.json` from its own knowledge, so the episode counts
  and descriptions weren't checked against an outside source
- wrote the automated tests and ran them, and checked the site from a fresh clone in a scripted
  Microsoft Edge browser session
- set up the virtual environment and made the commits, which list Claude as co-author

**My part was directing the project:**

- I gave Claude the assignment and the AI Use Policy
- Claude first suggested a video game backlog tracker, and I chose a TV show tracker instead
- after seeing screenshots, I asked for a darker color palette with red as the secondary color and a
  more visually appealing way to organize the site; Claude chose the specific design
- I asked for a way to request a show and a page displaying requested shows; Claude chose the details,
  including the statuses, the duplicate checks and the public listing
- I asked for an example request for Lanterns (2026); Claude wrote its network and note
- I asked for a security check; Claude tested the site, then added the login lockout, the pending request
  limit and the deployment settings
