from __future__ import annotations

from pathlib import Path


def parse_text(path: Path) -> list[dict]:
    """テキストファイルをそのまま読み込む。"""
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    return [{
        "text": text,
        "metadata": {"source": path.name},
    }]
