__all__ = ()

from django.test import SimpleTestCase

from bot.bot.ocr_text import assemble_lines


def box(x: float, y: float) -> list[list[float]]:
    return [[x, y], [x + 20, y], [x + 20, y + 10], [x, y + 10]]


class AssembleLinesTest(SimpleTestCase):
    def test_no_text_recognized(self) -> None:
        self.assertEqual(assemble_lines([]), "")

    def test_words_of_one_line_join(self) -> None:
        results = [[box(0, 0), "привет", 0.9], [box(25, 2), "мир", 0.9]]

        self.assertEqual(assemble_lines(results), "привет мир")

    def test_wide_gap_becomes_extra_space(self) -> None:
        results = [[box(0, 0), "привет", 0.9], [box(40, 0), "мир", 0.9]]

        self.assertEqual(assemble_lines(results), "привет   мир")

    def test_lines_are_split_by_vertical_gap(self) -> None:
        results = [[box(0, 0), "первая", 0.9], [box(0, 40), "вторая", 0.9]]

        self.assertEqual(assemble_lines(results), "первая\nвторая")

    def test_order_does_not_depend_on_input_order(self) -> None:
        results = [
            [box(30, 40), "четыре", 0.9],
            [box(0, 0), "один", 0.9],
            [box(0, 40), "три", 0.9],
            [box(30, 0), "два", 0.9],
        ]

        self.assertEqual(assemble_lines(results), "один два\nтри четыре")
