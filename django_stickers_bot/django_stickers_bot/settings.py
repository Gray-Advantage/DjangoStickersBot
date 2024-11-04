from pathlib import Path

from decouple import config, strtobool

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="some-secret-key", cast=str)
DEBUG = strtobool(config("DJANGO_DEBUG", "False"))

ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS",
    default="*",
    cast=lambda line: line.split(","),
)

INSTALLED_APPS = [
    "django.contrib.postgres",
    "bot.apps.BotConfig",
]

ROOT_URLCONF = "django_stickers_bot.urls"
WSGI_APPLICATION = "django_stickers_bot.wsgi.application"

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": (
#             BASE_DIR
#             / f"{config('DATANAR_DATABASE_NAME', default='db')}.sqlite3"
#         ),
#     },
# }
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": config("DATABASE_NAME"),
        "USER": config("DATABASE_USER"),
        "PASSWORD": config("DATABASE_PASSWORD"),
        "HOST": config("DATABASE_HOST"),
        "PORT": config("DATABASE_PORT"),
    },
}

AUTH_USER_MODEL = "users.User"

BOT_USE_WEBHOOK = strtobool(config("BOT_USE_WEBHOOK", "False"))
BOT_WEBHOOK_URL = config("BOT_WEBHOOK_URL", default="Not set", cast=str)
BOT_TOKEN = config("BOT_API_TOKEN", default="Not set", cast=str)
BOT_ADMIN_USER_IDS = config(
    "BOT_ADMIN_USER_IDS",
    default="",
    cast=lambda line: list(map(int, line.split(","))),
)

OCR_MODELS = BASE_DIR / "OCR_models"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
