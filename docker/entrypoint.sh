#!/bin/sh
set -eu

cd /app/site

python - <<'PY'
import os
import socket
import sys
import time
from urllib.parse import urlparse

database_url = os.environ.get("DATABASE_URL", "")
if not database_url:
    raise SystemExit(0)

parsed = urlparse(database_url)
host = parsed.hostname
port = parsed.port or 5432

deadline = time.time() + 60
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            raise SystemExit(0)
    except OSError:
        time.sleep(1)

print(f"Timed out waiting for database at {host}:{port}", file=sys.stderr)
raise SystemExit(1)
PY

python manage.py migrate --noinput

if [ "${BOOTSTRAP_FIXTURES:-0}" = "1" ]; then
  if ! python manage.py shell -c "from cms.models import Content; import sys; sys.exit(0 if Content.objects.exists() else 1)"; then
    python manage.py loaddata cms/fixtures/data_for_spanish_setup.json
    python manage.py loaddata group_manager/fixtures/data_for_spanish_experiments.json
  fi
fi

if [ "${COLLECTSTATIC:-0}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

exec "$@"
