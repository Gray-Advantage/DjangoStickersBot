from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "unused-no-http-endpoints"  # noqa: S105
DEBUG = False
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.postgres",
    "bot.apps.BotConfig",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DATABASE_NAME"),
        "USER": config("DATABASE_USER"),
        "PASSWORD": config("DATABASE_PASSWORD"),
        "HOST": config("DATABASE_HOST"),
        "PORT": config("DATABASE_PORT"),
    },
}

BOT_TOKEN: str = config("BOT_API_TOKEN")
BOT_ADMIN_USER_IDS: list[int] = config(
    "BOT_ADMIN_USER_IDS",
    default="",
    cast=lambda line: list(map(int, line.split(","))),
)

USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
