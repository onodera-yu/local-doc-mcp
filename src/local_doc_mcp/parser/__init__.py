from __future__ import annotations

from pathlib import Path

from local_doc_mcp.parser.pdf import parse_pdf
from local_doc_mcp.parser.excel import parse_excel
from local_doc_mcp.parser.image import parse_image
from local_doc_mcp.parser.text import parse_text

_DISPATCH: dict[str, callable] = {
    ".pdf": parse_pdf,
    ".xlsx": parse_excel,
    ".xls": parse_excel,
    ".png": parse_image,
    ".jpg": parse_image,
    ".jpeg": parse_image,
    ".bmp": parse_image,
    ".tiff": parse_image,
    ".tif": parse_image,
    ".txt": parse_text,
    ".md": parse_text,
    ".csv": parse_text,
    ".log": parse_text,
}


def parse_file(path: Path) -> list[dict]:
    """ファイル形式に応じたパーサーでドキュメントを解析する。

    Returns:
        list[dict]: 各要素は {"text": str, "metadata": dict} の形式
    """
    suffix = path.suffix.lower()
    parser = _DISPATCH.get(suffix)
    if parser is None:
        raise ValueError(f"未対応のファイル形式: {suffix} ({path.name})")
    return parser(path)
