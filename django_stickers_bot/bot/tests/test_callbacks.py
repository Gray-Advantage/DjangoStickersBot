__all__ = ()

from django.test import SimpleTestCase

from bot.bot.callbacks import (
    AddSetCallback,
    SetAction,
    SetCallback,
    StickerAction,
    StickerCallback,
)

CALLBACK_DATA_LIMIT = 64


class CallbackDataTest(SimpleTestCase):
    def test_set_callback_survives_round_trip(self) -> None:
        packed = SetCallback(action=SetAction.DELETE, set_id=7).pack()

        unpacked = SetCallback.unpack(packed)

        self.assertEqual(unpacked.action, SetAction.DELETE)
        self.assertEqual(unpacked.set_id, 7)

    def test_sticker_callback_survives_round_trip(self) -> None:
        packed = StickerCallback(
            action=StickerAction.EDIT,
            file_unique_id="AgADwGgAArnB6Eg",
        ).pack()

        unpacked = StickerCallback.unpack(packed)

        self.assertEqual(unpacked.action, StickerAction.EDIT)
        self.assertEqual(unpacked.file_unique_id, "AgADwGgAArnB6Eg")

    def test_add_set_callback_carries_nothing(self) -> None:
        self.assertEqual(AddSetCallback().pack(), "set_add")

    def test_everything_fits_telegram_limit(self) -> None:
        packed = (
            SetCallback(action=SetAction.SHOW, set_id=2**31).pack(),
            StickerCallback(
                action=StickerAction.SHOW,
                file_unique_id="A" * 32,
            ).pack(),
            AddSetCallback().pack(),
        )

        for data in packed:
            self.assertLessEqual(len(data.encode()), CALLBACK_DATA_LIMIT)
