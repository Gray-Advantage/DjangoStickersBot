#!/bin/sh
set -e

python manage.py migrate
python manage.py init_admins
exec python manage.py run_bot
