from http import HTTPStatus

from django.conf import settings
from django.http import HttpResponse
from django.views.generic.base import View
from telebot import types

from bot.bot.main import bot


class WebhookUpdate(View):
    def post(self, request):
        if settings.BOT_USE_WEBHOOK:
            json_str = request.body.decode("UTF-8")
            bot.process_new_updates([types.Update.de_json(json_str)])
            return HttpResponse(status=HTTPStatus.OK)
        return self.http_method_not_allowed(request)


__all__ = []
