# `language-debates-chat-system`

This repository contains the Django application used to run synchronous chat-based research experiments. It covers the full operational flow: participant onboarding, group assignment, timed question stages, live chat, admin monitoring, invitation management, and post-hoc external rating.

## Docker quick start

If you want the fastest path to a working local stack:

```bash
cp .env.docker.example .env.docker
docker compose up --build
docker compose run --rm web python manage.py createsuperuser
```

What happens automatically on `docker compose up --build`:

- PostgreSQL, Redis, MailHog, and the Django app start together
- the PostgreSQL database container is created if it does not exist yet
- Django waits for the database to become reachable
- Django runs `python manage.py migrate`
- if the database is empty and `BOOTSTRAP_FIXTURES=1`, Django loads the historical fixtures

What does **not** happen automatically:

- creating the Django superuser

## What this project does

The platform supports a staged experiment with three main roles:

- participants, who answer questions individually, discuss them in groups, and submit final answers
- staff/admin users, who invite participants, monitor activity, create groups, and export data
- external raters, who review completed chats and score them afterward

At a high level, the experiment flow is:

1. A participant logs in through a hashed invitation link.
2. The participant waits in `ws1` until a staff member assigns them to a group.
3. The participant completes an individual-answer stage (`s1`).
4. The group discusses selected questions in timed chat stages (`s2_1` to `s2_4`).
5. The participant completes a final individual-answer stage (`s3`).
6. Staff and external raters can later inspect, score, and export results.

## Repository scope

The codebase is being normalized to English, but historical research artifacts remain in Spanish where they document what real participants saw. Keep these intact unless the study protocol changes:

- `site/group_manager/fixtures/data_for_spanish_experiments.json`
- `site/cms/fixtures/data_for_spanish_setup.json`
- participant-facing CMS copy loaded from fixtures
- invitation email content in `site/templates/email_invitation.html`
- question wording, prompts, or stimuli used in the study

Safe places to translate or polish:

- source code, comments, identifiers, and logs
- staff/admin templates and operational copy
- developer documentation

## Stack

- Python 3
- Django 3.2
- Django Channels
- Daphne ASGI server
- SQLite for local development
- PostgreSQL on AWS Elastic Beanstalk deployments
- jQuery-based frontend with server-rendered templates

Key Python dependencies are listed in `site/requirements.txt`.

## Project layout

- `site/` Django project root
- `site/manage.py` Django management entrypoint
- `site/mysite/` project settings, ASGI/WSGI app, top-level URL routing
- `site/group_manager/` participant lifecycle, stage transitions, grouping, invitations, manager views
- `site/chat/` WebSocket chat app
- `site/cms/` editable content models and experiment fixtures
- `site/external_raters/` post-hoc review workflow
- `site/templates/` participant, staff, and rater templates
- `site/static/` frontend JavaScript and CSS

## Local setup

1. Clone the repository:

```bash
git clone https://github.com/facuzeta/chat-room-platform.git
cd chat-room-platform/site
```

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file that Django can read before startup:

```bash
cp .env.example .env
```

At minimum:

```env
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=127.0.0.1 localhost
DEBUG=True
```

Notes:

- `mysite/settings.py` reads environment variables with `django-environ`.
- The app loads `.env` from either the repository root or `site/.env`.
- Local development uses SQLite by default.
- You can switch to PostgreSQL by setting `DATABASE_URL`.
- Email, domain, Redis, and screener sync are all environment-driven now.

5. Create the database:

```bash
python manage.py makemigrations group_manager cms external_raters chat
python manage.py migrate
```

6. Load the baseline experiment data:

```bash
python manage.py loaddata cms/fixtures/data_for_spanish_setup.json
python manage.py loaddata group_manager/fixtures/data_for_spanish_experiments.json
```

7. Create an admin user:

```bash
python manage.py createsuperuser
```

## Running locally

Start the ASGI server with:

```bash
daphne mysite.asgi:application
```

If you only need standard Django endpoints and are not testing WebSockets, `runserver` can still be useful during development:

```bash
python manage.py runserver
```

## Docker development stack

The repository now includes a development Docker stack with:

- Django + Daphne
- PostgreSQL
- Redis
- MailHog for local email capture

### First-time setup

1. Copy the Docker environment template:

```bash
cp .env.docker.example .env.docker
```

2. Build and start the stack:

```bash
docker compose up --build
```

3. Create an admin user in the running container:

```bash
docker compose run --rm web python manage.py createsuperuser
```

### Database and migrations behavior

The Docker entrypoint already handles the core bootstrap:

- database creation is handled by the `postgres` container itself
- Django migrations run automatically every time the `web` container starts
- fixtures load automatically only when the database appears empty

That behavior is implemented in `docker/entrypoint.sh`.

### What Docker config does

- `DATABASE_URL` points Django to the bundled PostgreSQL container.
- `REDIS_URL` enables a Redis-backed Channels layer.
- `EMAIL_HOST=mailhog` routes invitation emails to MailHog instead of a real SMTP provider.
- `BOOTSTRAP_FIXTURES=1` loads the historical fixtures only when the database is empty.
- `ENABLE_SCREENER_SYNC=False` avoids depending on the external Google Sheet during local Docker runs.

### Useful Docker endpoints

- app: `http://localhost:8000`
- MailHog UI: `http://localhost:8025`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

## Run the experiment locally

This is the recommended path for someone who wants to reproduce the application behavior after cloning the repository.

### 1. Start the stack

```bash
cp .env.docker.example .env.docker
docker compose up --build
docker compose run --rm web python manage.py createsuperuser
```

Then open:

- app: `http://localhost:8000`
- Django admin: `http://localhost:8000/admin/`
- manager dashboard: `http://localhost:8000/manager`
- MailHog: `http://localhost:8025`

### 2. Sign in as staff

Use the superuser you just created and log into:

- `/admin/` for raw model access
- `/manager` for the staff workflow UI

### 3. Create participants

The simplest path is:

- open `/manager/invite_participants`
- create one or more participants
- save the generated records

You can also inspect or edit them later in `/admin/`.

### 4. Send or inspect invitation emails

When using the Docker setup, invitation emails do not go to real inboxes.

- the app sends them to MailHog
- open `http://localhost:8025`
- inspect the captured email
- copy the participant login link from there

### 5. Open participant sessions

Each participant enters the experiment through a URL like:

```text
/login?hash=<participant-hash>
```

You can get that link either:

- from the invitation email shown in MailHog
- or by inspecting the participant record in the admin/manager views

If you want to simulate multiple participants, open multiple browser windows or profiles and log in with different hashes.

### 6. Move participants into a group

Participants first wait in `ws1`.

To start an experiment session:

- open `/manager`
- wait until participants appear as connected
- select the participants
- choose the experiment
- create the group

That action moves them from the waiting stage into the first individual-answer stage.

### 7. Run through the experiment

The expected stage flow is:

1. `ws1` waiting room
2. `s1` individual answers
3. `s2_1` to `s2_4` timed chat/discussion stages
4. `s3` final individual answers
5. `thanks`

During this flow:

- participants interact through the browser UI
- staff can monitor progress from `/manager/groups_list`
- individual sessions can be inspected in `/manager/group_status/<group_id>`

### 8. Review exported data

Once you have completed at least one session, you can inspect the resulting data:

- open `/manager/export_all` as a staff user
- review grouped answers, chats, and expert-evaluation data as JSON

### 9. Use the external rater workflow

To exercise the post-hoc rating flow:

- create an external rater entry
- open the corresponding route under `/external_raters/`
- score completed chat stages

The manager and external-rater templates expose the operational flow, but they assume experiment data already exists.

## What the fixtures provide

The bundled fixtures give you:

- baseline CMS content
- experiment definitions
- question text
- configuration needed for the historical experiment setup

They do not create:

- a Django superuser
- active participant browser sessions
- completed chats
- external rater records ready to use

Those still need to be created through the application workflow.

## Main routes

Useful routes during development:

- participant login: `/login?hash=<participant-hash>`
- participant home: `/home`
- manager dashboard: `/manager`
- invitation management: `/manager/invite_participants`
- groups overview: `/manager/groups_list`
- Django admin: `/admin/`
- external raters: `/external_raters/`

Top-level routes are defined in `site/mysite/urls.py`.

## Common tasks

Typical maintenance and admin tasks:

- Apply new schema changes:

```bash
python manage.py makemigrations
python manage.py migrate
```

- Reload the baseline fixtures after resetting a local database:

```bash
python manage.py loaddata cms/fixtures/data_for_spanish_setup.json
python manage.py loaddata group_manager/fixtures/data_for_spanish_experiments.json
```

- Create a participant access link:
  create or inspect the participant in `/admin/` or `/manager/invite_participants`, then use `/login?hash=<participant-hash>`.

- Invite participants in bulk:
  use `/manager/invite_participants`, which supports both single-record editing and email-list creation.

- Create groups for active participants:
  use `/manager`, review connected participants, then assign them to an experiment and create a group.

- Review a group session:
  open `/manager/groups_list`, then drill into `/manager/group_status/<group_id>`.

- Export all experiment data as JSON:
  open `/manager/export_all` while authenticated as staff.

- Score chats as an external rater:
  use the routes under `/external_raters/` after creating a rater record.

- Re-run a lightweight Python validation:

```bash
python3 -m compileall site/group_manager site/external_raters site/mysite
```

- Start the full Docker stack:

```bash
docker compose up --build
```

- Stop the Docker stack:

```bash
docker compose down
```

- Reset the Docker database volume:

```bash
docker compose down -v
```

## Operational notes

- Local development uses the in-memory Channels layer configured in `site/mysite/settings.py`.
- Production should use a Redis-backed Channels layer for multi-worker WebSocket support.
- `update_screener_google_form()` pulls screener data from a Google Sheet and is triggered from the manager dashboard.
- Invitation emails are rendered from `site/templates/email_invitation.html`.
- Group creation and stage-transition logic lives primarily in `site/group_manager/services.py`.
- For local Docker runs, MailHog captures outbound email so no real invitations are sent.

## Data and content

There are two main fixture sources:

- `cms/fixtures/data_for_spanish_setup.json` for CMS content and interface copy
- `group_manager/fixtures/data_for_spanish_experiments.json` for experiments, questions, and related setup

Because those fixtures represent the historical experiment setup, treat them as research artifacts rather than generic seed data.

## Recommended developer workflow

When making maintenance changes:

1. Keep participant-visible experiment content stable unless the protocol changes.
2. Prefer English for code, docs, staff-facing views, and internal logs.
3. Validate Python changes with `python3 -m compileall` or the relevant Django command.
4. Be careful around manager flows, invitation logic, and chat-stage timing, since they affect the experiment state machine.

## Documentation conventions

- Preserve experimental Spanish when it is part of the study record.
- Prefer English for code, comments, docs, internal tooling, and staff-facing UI.
- If a string is ambiguous, treat participant-visible copy as research material unless proven otherwise.

## Known limitations

- Some participant-facing labels are still intentionally embedded in Spanish because they are part of the original experiment record.
- The local setup depends on loading historical fixtures rather than a generalized bootstrap command.
- The screener sync still depends on an external Google Sheet when `ENABLE_SCREENER_SYNC=True`.
- WebSocket and email settings are now environment-driven, but production deployment still needs explicit infra choices for PostgreSQL, Redis, and SMTP.
