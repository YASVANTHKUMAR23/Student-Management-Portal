# Student Management System

A Django-based Student Management System with authentication, profile
management, and full CRUD for student records.

## Features

- **Authentication (browser)**: register, login, logout (CSRF-safe, POST-only),
  forgot-password / reset-password by email, change-password for logged-in
  users, Django's built-in password validators.
- **Authentication (API)**: JWT-based auth under `/api/` for external
  clients (mobile apps, SPAs, Postman, etc.) — see "JWT API" section below.
- **Authorization**: every data page requires login; `next=` redirects are
  validated to prevent open-redirect attacks.
- **Role-based session management**: three account types (Admin, Teacher,
  Student), each with different page access **and** a different session
  lifetime — see "Roles & Session Management" below.
- **Predefined courses & teacher assignment**: courses are a managed,
  predefined catalog (dropdown-only, no free text); Admins assign
  teachers to the courses they teach, and students are assigned both a
  course and a teacher — see "Courses & Assignments" below.
- **Stricter email validation**: every form collecting an email gives a
  specific "must contain an '@'" message rather than a generic error.
- **Students CRUD**: add / edit / delete / view student records, with
  server-side validation (age range, phone format, unique email) — both in
  the browser UI and via the JWT API.
- **Search & filter**: search by name/email/city, filter by course, both
  combined with pagination (filters are preserved across pages). Available
  in both the browser UI and the API.
- **Dashboard**: totals, latest students, and a Chart.js bar chart of
  students per course.
- **Profiles**: profile picture upload (with a generated default avatar),
  bio, join date.
- **UI**: Bootstrap 5, responsive layout, flash messages, custom
  `static/css/style.css` for polish, custom 403/404/500 error pages.
- **Admin**: Django admin configured with list/search/filter for both
  models.
- **Tests**: `practice/tests.py` covers models, browser auth/CRUD flows,
  and the full JWT API lifecycle (register → obtain → refresh → logout).

## What was fixed / added on top of the original project

| Area | Change |
|---|---|
| Back-button after logout | Protected pages (and the login/register pages) now send `Cache-Control: no-store`, so the browser can't serve a stale cached copy of an authenticated page when you press Back after logging out — it always re-checks with the server, which correctly redirects to `/login/`. |
| Email validation | Every form collecting an email (register, add/edit student, edit profile) now gives an explicit "must contain an '@'" message, on top of Django's built-in format validation. |
| Error message styling | Django's default `messages.error()` tag ("error") doesn't map to any real Bootstrap class — only `alert-danger` exists — so invalid-login and other error messages rendered unstyled/invisible. Added `MESSAGE_TAGS` in settings.py so they now render as a visible red alert, exactly like the "Welcome back" success alert. |
| Courses | Converted from a free-text field (anyone could type anything, leading to duplicates like "CS"/"cs"/"Computer Science") to a managed `Course` table with a dropdown — see "Courses & Assignments" below. Existing data was preserved during the migration. |
| Teacher assignment | Added a `Profile.courses` M2M and an Admin-only `/assign-teacher-courses/` page to assign teachers to the courses they teach. |
| Student assignment | Added `Student.teacher`, so each student can be assigned both a course and a teacher via dropdowns on the add/edit form. |
| `login_user` view | Now respects a safe `?next=` parameter after login instead of always redirecting to `students` (fixes `@login_required` redirects landing on the wrong page). |
| `logout_user` view | Changed from a GET link to a CSRF-protected POST-only action (a bare `<a href="/logout/">` is a classic CSRF/clickjacking vector). |
| `students` view/template | Pagination previously dropped the `search` query string when navigating between pages. Also added a course filter dropdown. |
| `Student` model | `age` is now a validated `PositiveIntegerField` (1-120), `phone` is validated with a regex, added `created_at`/`updated_at` timestamps and default ordering. |
| Forms | Added a `BootstrapFormMixin` so all custom forms render with Bootstrap classes (previously `{{ form.as_p }}` produced unstyled `<input>`s); added extra `clean_*` validation (duplicate email, empty name). |
| Profile picture | The default profile picture (`default.png`) is now an actual generated placeholder image so `{{ user.profile.profile_picture.url }}` never 404s. |
| Password management | Added full "forgot password" (email-based reset) and "change password" flows using Django's built-in class-based views, styled to match the rest of the app. |
| Static/media | Configured `STATICFILES_DIRS`/`STATIC_ROOT`, added WhiteNoise for production static serving, added a small custom stylesheet. |
| Settings | `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, email settings, and security flags are now driven by environment variables (see `.env.example`) instead of being hard-coded, so the same code works in dev and production. |
| Error pages | Added `403.html` / `404.html` / `500.html` templates (used automatically once `DEBUG=False`). |
| Admin | Registered models with `list_display`, `search_fields`, `list_filter` instead of the bare `admin.site.register(...)`. |
| Tests | Added a test suite (was an empty stub). |

## Roles & Session Management

Every account has a **role** — `Admin`, `Teacher`, or `Student` — stored on
`Profile.role`. Django's session framework (`django.contrib.sessions`) is
used to enforce two different things per role, both visible in a live
demo:

### 1. Different permissions per role

| Role | Can view | Can add/edit/delete students | Notes |
|---|---|---|---|
| **Admin** | Everything | Yes | Full access; also has `/admin/` (Django admin site) |
| **Teacher** | Everything | Yes | Same student-management access as Admin |
| **Student** | Only their **own** linked record | No | Redirected away from the full list; direct URL access to another student's record returns `403 Forbidden` |

This is enforced two ways in the code:
- `practice/decorators.py` — a `role_required(*roles)` decorator, applied
  to `add_student`, `edit_student`, `delete_student` in `views.py`.
- Manual checks inside `students` and `student_detail` in `views.py` (a
  Student is redirected to their own record instead of the full list; a
  `PermissionDenied` is raised, rendering `403.html`, if they try to view
  someone else's).

### 2. Different session lifetime per role

On login (`login_user` in `views.py`), `request.session.set_expiry(...)`
is called with a different duration depending on the account's role:

```python
SESSION_LIFETIME_SECONDS = {
    "admin":   60 * 60 * 24,   # 24 hours
    "teacher": 60 * 60 * 12,   # 12 hours
    "student": 60 * 60 * 2,    # 2 hours
}
```

The `/profile/` page shows the *actual* computed expiry time and
remaining lifetime for the current session, so you can visibly confirm
this — log in as different roles and compare the numbers shown.

### How to link a Student account to a Student record

A "Student" role account only ever sees a record if `Student.linked_user`
points at their `User`. This is intentionally not self-service (a student
shouldn't be able to claim any record) — link it via `/admin/`:

1. Log in to `/admin/` as an Admin
2. Go to **Practice → Students**, open a student, set **Linked user** to
   the relevant account, save

(The seed data already links the `satvik` student record to the `Satvik`
user account as an example.)

### Demo script (for showing your teacher)

1. Register two accounts at `/register/` — one as **Teacher**, one as
   **Student** (the role selector is right there on the form).
2. Log in as the **Teacher** → you can see "Students" and "Add Student" in
   the nav, add/edit/delete freely.
3. Log out, log in as the **Student** → the nav only shows "My Record";
   visiting `/add-student/` directly redirects you away with a "you don't
   have permission" message.
4. Visit `/profile/` as each role → point out the "Session info" box
   showing a different expiry time per role.
5. (Optional) As the Student, try visiting another student's URL directly
   (e.g. `/student/1/` if it isn't yours) → show the `403 Forbidden` page.

## Courses & Assignments

Courses are no longer free-text — they're a managed `Course` table, and
every place that used to accept typed-in course names is now a dropdown
sourced from that table.

### Managing the course catalog

Admins manage the list of courses at `/admin/` → **Practice → Courses**
(add, rename, delete). The project ships with 11 predefined courses
(B.Tech CS/IT/ECE/ME/CE, BCA, MCA, B.Sc Mathematics, B.Com, MBA, and AI &
ML) — add more the same way.

### Assigning teachers to courses

Only Admins can do this, at **"Assign Courses"** in the nav (or
`/assign-teacher-courses/`):
1. Pick a teacher from the dropdown, click **Load**.
2. Select every course they should teach (multi-select — hold Ctrl/Cmd to
   pick more than one) and **Save**.
3. The right-hand panel shows every teacher's current assignments at a
   glance.

A teacher can see their own assigned courses on their `/profile/` page.

### Assigning a student to a course and a teacher

The **Add/Edit Student** form now has two dropdowns instead of one text
field:
- **Course** — required, chosen from the predefined catalog.
- **Teacher** — optional, limited to accounts with the Teacher role.

Both are ordinary Django `ForeignKey` dropdowns — a student can't be
saved with a course or teacher that doesn't exist in the system.

## JWT API

Everything under `/api/` is a separate, stateless JWT-authenticated REST
API — it coexists with the browser pages and doesn't affect them. It uses
[Django REST Framework](https://www.django-rest-framework.org/) +
[djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/).

| Method | Endpoint | Auth required | Description |
|---|---|---|---|
| POST | `/api/register/` | No | Create a new account |
| POST | `/api/token/` | No | Log in — exchange username/password for an access + refresh token pair |
| POST | `/api/token/refresh/` | No (needs refresh token) | Exchange a refresh token for a new access token |
| POST | `/api/token/verify/` | No | Check whether a token is still valid |
| POST | `/api/logout/` | Yes | Blacklist a refresh token (body: `{"refresh": "..."}`) |
| GET | `/api/me/` | Yes | Get the logged-in user's account + profile |
| GET | `/api/students/` | Yes | List students (paginated, `?search=`, `?course=`, `?city=`, `?ordering=`) |
| POST | `/api/students/` | Yes | Create a student |
| GET | `/api/students/{id}/` | Yes | Retrieve one student |
| PUT/PATCH | `/api/students/{id}/` | Yes | Update a student |
| DELETE | `/api/students/{id}/` | Yes | Delete a student |

Access tokens are short-lived (15 minutes by default); refresh tokens last
7 days and rotate on each use (the old one is blacklisted automatically).
Both lifetimes are configurable via `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` and
`JWT_REFRESH_TOKEN_LIFETIME_DAYS` environment variables.

### Example usage (curl)

```bash
# Register
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"Str0ng!Pass99","password2":"Str0ng!Pass99"}'

# Log in — get access + refresh tokens
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"Str0ng!Pass99"}'
# => {"access": "...", "refresh": "..."}

# Call a protected endpoint
curl http://127.0.0.1:8000/api/students/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# Create a student
curl -X POST http://127.0.0.1:8000/api/students/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","age":21,"course":"CS","email":"john@example.com","phone":"9876543210","city":"Delhi"}'

# Refresh the access token when it expires
curl -X POST http://127.0.0.1:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<REFRESH_TOKEN>"}'

# Log out (blacklist the refresh token)
curl -X POST http://127.0.0.1:8000/api/logout/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<REFRESH_TOKEN>"}'
```

## Design decisions / assumptions

- The browser-facing site keeps using Django's session authentication —
  that's the right fit for server-rendered pages (built-in CSRF
  protection, no token storage headaches). JWT was added **alongside** it,
  under `/api/`, for API clients (mobile apps, a separate SPA frontend,
  Postman/automation) that can't rely on cookies. The two auth systems are
  independent: a session cookie won't authenticate `/api/` requests, and a
  JWT won't log you into the template pages.
- `djangorestframework-simplejwt`'s token blacklist app is enabled so
  `/api/logout/` can actually invalidate a refresh token, rather than just
  relying on client-side token deletion (which doesn't stop a leaked token
  from being reused).
  switching to PostgreSQL only requires changing `DATABASES` (and adding
  `psycopg2`), the rest of the code is database-agnostic.
- Email sending for password reset defaults to Django's **console backend**
  in development, so you can test the "forgot password" flow locally
  without configuring a real mailbox — the reset link is printed to the
  terminal running `runserver`.

## Project structure

```
DjangoPR/
├── manage.py
├── requirements.txt
├── .env.example
├── db.sqlite3
├── myproject/            # project settings/urls
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── practice/              # main app
│   ├── models.py          # Student, Profile, Course
│   ├── views.py           # browser (session-auth) views
│   ├── api_views.py       # JWT-authenticated API views
│   ├── serializers.py     # DRF serializers for the API
│   ├── forms.py
│   ├── urls.py            # browser routes
│   ├── api_urls.py        # /api/ routes
│   ├── admin.py
│   ├── signals.py         # auto-create Profile on user creation
│   ├── tests.py
│   ├── migrations/
│   └── templates/         # all HTML templates
├── static/
│   ├── css/style.css
│   └── img/default.png
└── media/
    ├── default.png         # default profile picture
    └── profile_pictures/
```

## Setup — run from scratch

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional but recommended) copy the example environment file
cp .env.example .env            # then edit values as needed, or just
                                 # export them in your shell

# 4. Apply database migrations
python manage.py migrate

# 5. Create an admin user (optional, for /admin/)
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/register/` to create an account, or
`http://127.0.0.1:8000/admin/` to log in as the superuser.

### Running tests

```bash
python manage.py test practice
```

### Production checklist

- Set `DJANGO_DEBUG=False` and a real `DJANGO_SECRET_KEY`.
- Set `DJANGO_ALLOWED_HOSTS` to your real domain(s).
- Run `python manage.py collectstatic` (WhiteNoise serves the results).
- Configure real SMTP credentials (`DJANGO_EMAIL_*`) if you want password
  reset emails to actually be delivered.
- Consider switching `DATABASES` to PostgreSQL for production traffic.

## Dependencies

- `Django` — web framework
- `Pillow` — required for `ImageField` (profile pictures)
- `whitenoise` — serves static files in production without a separate web
  server/CDN
- `djangorestframework` — powers the `/api/` endpoints
- `djangorestframework-simplejwt` — JWT issuing/refresh/blacklisting for the API
- `django-filter` — `?course=`/`?city=` filtering on `/api/students/`
