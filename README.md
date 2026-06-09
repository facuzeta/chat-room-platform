# `language-debates-chat-system`

This repository contains the Django application used to run synchronous chat-based research experiments. It covers the full operational flow: participant onboarding, group assignment, timed question stages, live chat, admin monitoring, invitation management, and post-hoc external rating.

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

For the working rule used in this branch, see `docs/translation-boundary.md`.

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
- `docs/` developer-facing repository notes

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

4. Create a `.env` file that Django can read before startup. At minimum:

```env
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=127.0.0.1 localhost
EMAIL_HOST_PASSWORD=your-email-password
DEBUG=True
```

Notes:

- `mysite/settings.py` reads environment variables with `django-environ`.
- Local development uses SQLite by default.
- Production database settings switch automatically when AWS RDS variables are present.

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

## Operational notes

- Local development uses the in-memory Channels layer configured in `site/mysite/settings.py`.
- Production should use a Redis-backed Channels layer for multi-worker WebSocket support.
- `update_screener_google_form()` pulls screener data from a Google Sheet and is triggered from the manager dashboard.
- Invitation emails are rendered from `site/templates/email_invitation.html`.
- Group creation and stage-transition logic lives primarily in `site/group_manager/services.py`.

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
- WebSocket deployment settings are minimal for local use and should be reviewed before production reuse.
