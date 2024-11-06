FROM python:3.12.4-slim

COPY ./requirements /requirements
RUN pip install -r requirements/prod.txt
RUN rm -rf requirements

COPY ./django_stickers_bot /django_stickers_bot/
COPY ./for_docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
WORKDIR /django_stickers_bot

ENTRYPOINT ["../entrypoint.sh"]
