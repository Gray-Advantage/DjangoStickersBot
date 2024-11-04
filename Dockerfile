FROM python:3.12.4-slim

COPY ./requirements /requirements
RUN pip install -r requirements/prod.txt
RUN rm -rf requirements

COPY ./django_stickers_bot /django_stickers_bot/
WORKDIR /django_stickers_bot

CMD python manage.py migrate \
 && python manage.py init_admins \
 && python manage.py runserver
# &&
# && gunicorn datanar.wsgi:application \
#    --workers $(nproc) \
#    --bind 0.0.0.0:8000 \
#    --access-logfile /datanar/logs/gunicorn_access.log \
#    --error-logfile /datanar/logs/gunicorn_error.log