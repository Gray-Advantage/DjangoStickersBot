from decouple import config
from django.core.management.base import BaseCommand

from bot.models import TelegramUser


class Command(BaseCommand):
    help = "Create or update admins"

    def handle(self, *args, **options):
        admin_ids = config(
            "BOT_ADMIN_USER_IDS",
            default="",
            cast=lambda line: list(map(int, line.split(","))),
        )
        for admin_id in admin_ids:
            TelegramUser.objects.update_or_create(
                telegram_id=admin_id,
                defaults={"is_admin": True},
            )
        self.stdout.write(
            self.style.SUCCESS("Admins created successfully!"),
        )


__all__ = []
