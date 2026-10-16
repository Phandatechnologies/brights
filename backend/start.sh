#!/bin/sh
# Container start-up: apply database changes, then start the web server.
set -e

python manage.py migrate --noinput
python manage.py createcachetable

# Access log records the path WITHOUT the query string (%(U)s), so one-time tokens in
# email links (/verify-email?uid=…&token=…) never end up in the logs.
exec gunicorn config.wsgi \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 60 \
  --access-logfile - \
  --access-logformat '%(t)s "%(m)s %(U)s" %(s)s %(b)s %(M)sms'
