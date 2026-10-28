# MediBook Clinic Appointments (IT 424 Test III + Test IV)

Django server-rendered clinic booking demo using Django templates/forms, HTMX for HTML partial exchanges, and Alpine.js for small client-only UI state. No React, Vue, jQuery, or build step is used.

## Requirements
- Python 3.10+
- Django 5.2 (installed from `requirements.txt`)
- Pillow for doctor photo uploads
- SQLite (included with Python)

## Run locally (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py makemigrations clinic
python manage.py migrate
python manage.py seed_demo
python manage.py check
python manage.py test clinic -v 2
python manage.py runserver
```
Open http://127.0.0.1:8000/. Staff pages are intentionally open for this practical exam: `/manage/doctors/` and `/manage/appointments/`. Create an admin with `python manage.py createsuperuser` to use `/admin/`.

## Demo data and fixture
`python manage.py seed_demo` creates seven specialties/doctors idempotently. Use Django Admin to add, edit, or remove sample records. The `clinic/fixtures/demo.json` fixture can also be loaded with `python manage.py loaddata demo` after migrations.

## Hosting decisions
- **HTMX:** loaded from the pinned HTMX 2.0.4 CDN URL in `base.html`; no bundler is required. HTMX requests ask Django for HTML partials, and Django remains the source of truth for search, pagination, validation, bookings, and statuses. For offline assessment, download the HTMX distribution and point the script tag to a local static file.
- **Alpine.js:** loaded as a pinned 3.14.8 CDN version with `defer`; the Alpine Persist plugin is loaded before Alpine core. Alpine manages menus, tabs, theme/view preferences, toast state, and wizard UI only. No database-owned data is stored in Alpine.
- **Static/media:** CSS and Alpine component definitions are under `clinic/static/clinic/css/` and `clinic/static/clinic/js/`. Doctor uploads use `MEDIA_ROOT` / `MEDIA_URL` during development.

## Alpine component inventory
| Component | Page | State / getters | Directives/events | Scope/store |
|---|---|---|---|---|
| appShell | All pages | menuOpen | x-data, x-init, x-show, x-transition, @click, @keydown.escape.window | inline component + theme/toasts stores |
| searchBox | Directory | query | x-model, x-ref, @keydown.slash.window, x-show | local input state; HTMX submits search |
| gridView | Directory | view | x-data, :class, @click, :aria-pressed | persisted layout store |
| doctorCard | Directory | expanded | @mouseenter, @mouseleave, x-show, x-transition, x-cloak | local per-card state |
| tabs | Doctor detail | active, tabs | x-for with :key, x-show, :aria-selected, arrow keys | local tab state |
| bookingWizard | Booking | step, reason; canAdvance, stepName, remaining | x-show, x-text, :disabled, x-model, $watch, $nextTick | local UI state; server validates all data |
| appointmentFilters | Staff appointments | active; counts | x-show, x-text, :class, x-for | local status filter based on server-rendered rows |
| cancelDialog | Staff appointments | open, url, reference | role=dialog, @keydown.escape.window, @click.self, $dispatch/listener | local dialog state; HTMX posts status update |
| theme store | All pages | dark, toggle() | :class, $persist | shared persisted UI preference |
| toasts store | All pages | items, add(), remove() | x-for, :key, x-transition, @toast.window | shared temporary notification state |

## State map
- **Local `x-data`:** menu visibility, expanded doctor card, active tab, wizard step and typed reason preview, active appointment-status tab, and modal visibility. These states are transient presentation choices.
- **Shared `Alpine.store`:** theme preference, doctor grid/list preference, and toast stack because multiple components or pages use them.
- **Django-owned:** doctor and specialty records, appointment records, booked slots, server-side field validation, booking conflict detection, status changes, and reference numbers. Alpine never persists or rebuilds these records.

## Alpine + HTMX integration points
1. Directory search, specialty filter, sorting, and pagination send HTMX GET requests; Django returns the grid partial and Alpine's small grid/list preference applies to the swapped cards.
2. Booking date changes request the server-rendered available-slot partial. The server disables booked slots and the form repeats conflict validation on POST.
3. Booking form submits with `hx-post`; Django returns field errors in a 422 partial response or an `HX-Redirect` header after success. The wizard component is outside the swapped field partial so its step state remains.
4. Staff confirm/cancel and doctor accepting toggles use HTMX row swaps. HTMX events toggle loading feedback and the shared toast store receives notification events.
5. CSRF is supplied using the `hx-headers` attribute in `base.html` and `{% csrf_token %}` in every POST form.

## Validation and data-entry analysis
- **AppointmentForm:** patient name required (Django max length 120); email must be valid if supplied and required for Teleconsultation; phone must match `09XXXXXXXXX` or `+639XXXXXXXXX`; appointment date cannot be past or Sunday; time slot must be one of the six fixed slots and must not already be booked for that doctor/date; visit type must be In-Clinic or Teleconsultation; reason must be at least 10 and at most 300 characters.
- **DoctorForm:** name required, up to 120 characters; specialty must be an existing Specialty; bio required and up to 1,500 characters; fee must be greater than zero; photo optional image upload; accepting checkbox controls new bookings.

## Security / limitations
This is an educational practical build. Staff URLs are deliberately open as the exam specifies. Before production, add authentication/authorization, configure a secret key and DEBUG/ALLOWED_HOSTS, validate image size/type, and use a production database. Run the tests before submission and capture actual screenshots; do not claim test points without evidence.
