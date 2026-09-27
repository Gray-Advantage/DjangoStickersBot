__all__ = ("EMPTY_TEXT", "assemble_lines")

from typing import Any

EMPTY_TEXT = "<Пусто>"

VERTICAL_SHIFT = 15
HORIZONTAL_SHIFT = 10


def assemble_lines(
    results: list[Any],
    vertical_shift: int = VERTICAL_SHIFT,
    horizontal_shift: int = HORIZONTAL_SHIFT,
) -> str:
    if not results:
        return ""

    results.sort(key=lambda item: min(point[1] for point in item[0]))

    lines: list[list[Any]] = []
    current_line: list[Any] = []
    current_y = min(point[1] for point in results[0][0])

    for item in results:
        min_y = min(point[1] for point in item[0])
        if abs(min_y - current_y) > vertical_shift:
            lines.append(current_line)
            current_line, current_y = [item], min_y
        else:
            current_line.append(item)

    if current_line:
        lines.append(current_line)

    return "\n".join(_join_line(line, horizontal_shift) for line in lines)


def _join_line(line: list[Any], horizontal_shift: int) -> str:
    line.sort(key=lambda item: min(point[0] for point in item[0]))

    parts: list[str] = []
    last_x: float | None = None
    for word in line:
        min_x = min(point[0] for point in word[0])
        if last_x is not None and min_x - last_x > horizontal_shift:
            parts.append(" ")

        parts.append(word[1])
        last_x = max(point[0] for point in word[0])

    return " ".join(parts)
