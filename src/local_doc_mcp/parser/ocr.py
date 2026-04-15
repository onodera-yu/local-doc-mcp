"""OCRの共有ユーティリティ。PDF・Excel・画像パーサーから利用する。"""
from __future__ import annotations

import numpy as np
from rapidocr_onnxruntime import RapidOCR

_ocr: RapidOCR | None = None


def get_ocr() -> RapidOCR:
    """RapidOCR のシングルトンを返す。"""
    global _ocr
    if _ocr is None:
        _ocr = RapidOCR()
    return _ocr


def ocr_from_image_bytes(data: bytes) -> str:
    """画像バイナリからOCRでテキストを抽出する。"""
    arr = np.frombuffer(data, dtype=np.uint8)
    result, _ = get_ocr()(arr)
    if not result:
        return ""
    return "\n".join(line[1] for line in result)
