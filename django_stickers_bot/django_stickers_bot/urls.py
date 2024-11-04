from django.urls import include, path

urlpatterns = [
    path("bot/", include("bot.urls")),
]


__all__ = []
