FROM python:3.12.14-slim

COPY ./requirements /requirements
RUN pip install --no-cache-dir -r requirements/prod.txt \
    && HEADLESS="$(grep -i '^opencv-python-headless' requirements/prod.txt)" \
    && pip uninstall -y opencv-python \
    && pip install --no-cache-dir --force-reinstall "$HEADLESS" \
    && rm -rf requirements

ENV PYTHONUNBUFFERED=1

COPY ./django_stickers_bot /django_stickers_bot/
COPY ./for_docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
WORKDIR /django_stickers_bot

RUN python -c "from bot.bot.ocr_worker import build_engine; build_engine()"

ENTRYPOINT ["../entrypoint.sh"]
