__all__ = ("build_engine",)

import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from rapidocr import (
    EngineType,
    LangDet,
    LangRec,
    ModelType,
    OCRVersion,
    RapidOCR,
)
from rapidocr.utils.output import RapidOCROutput

from bot.bot.ocr_text import assemble_lines

REC_LANG = LangRec.CYRILLIC
THREADS = 4
TEXT_SCORE = 0.5

BACKGROUNDS = ((255, 255, 255), (128, 128, 128))
MIN_MEAN_SCORE = 0.6


def build_engine() -> RapidOCR:
    return RapidOCR(
        params={
            "Det.engine_type": EngineType.ONNXRUNTIME,
            "Det.lang_type": LangDet.CH,
            "Det.model_type": ModelType.MOBILE,
            "Det.ocr_version": OCRVersion.PPOCRV5,
            "Rec.engine_type": EngineType.ONNXRUNTIME,
            "Rec.lang_type": REC_LANG,
            "Rec.model_type": ModelType.MOBILE,
            "Rec.ocr_version": OCRVersion.PPOCRV5,
            "Global.use_cls": False,
            "Global.text_score": TEXT_SCORE,
            "EngineConfig.onnxruntime.intra_op_num_threads": THREADS,
        },
    )


def flatten(path: Path, background: tuple[int, int, int]) -> np.ndarray:
    with Image.open(path) as img:
        rgba = img.convert("RGBA")
        flat = Image.new("RGB", rgba.size, background)
        flat.paste(rgba, mask=rgba.split()[3])
        return np.array(flat)


def recognize(engine: RapidOCR, path: Path) -> str:
    best_text = ""
    best_score = -1.0

    for background in BACKGROUNDS:
        result = engine(flatten(path, background))
        if not isinstance(result, RapidOCROutput):
            continue

        boxes = result.boxes
        texts = result.txts
        scores = result.scores
        if boxes is None or texts is None or scores is None:
            continue

        mean_score = float(np.mean(scores))
        if mean_score > best_score:
            best_score = mean_score
            best_text = assemble_lines(
                [
                    [box.tolist(), text, score]
                    for box, text, score in zip(
                        boxes,
                        texts,
                        scores,
                        strict=False,
                    )
                ],
            )

        if mean_score >= MIN_MEAN_SCORE:
            break

    return best_text


def main() -> None:
    folder = Path(sys.argv[1])
    engine = build_engine()
    texts = {
        path.name: recognize(engine, path)
        for path in sorted(folder.iterdir())
        if path.is_file()
    }
    sys.stdout.write(json.dumps(texts, ensure_ascii=False))


if __name__ == "__main__":
    main()
