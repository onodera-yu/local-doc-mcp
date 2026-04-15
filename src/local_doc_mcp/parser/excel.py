from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import openpyxl

from local_doc_mcp.parser.ocr import ocr_from_image_bytes


def _extract_images_from_xlsx(path: Path) -> dict[str, list[str]]:
    """XLSXファイルから埋め込み画像を抽出しOCRでテキスト化する。

    Returns:
        シート名 → OCRテキストのリスト のマッピング
    """
    sheet_images: dict[str, list[str]] = {}
    try:
        with ZipFile(path) as zf:
            # xl/drawings/以下の画像ファイルを取得
            image_files = [n for n in zf.namelist() if n.startswith("xl/media/")]
            for img_name in image_files:
                image_bytes = zf.read(img_name)
                text = ocr_from_image_bytes(image_bytes)
                if text:
                    # 画像とシートの紐付けが困難なため、全体としてまとめる
                    sheet_images.setdefault("_all", []).append(text)
    except Exception:
        pass
    return sheet_images


def parse_excel(path: Path) -> list[dict]:
    """Excelファイルをシート単位で文章化する。埋め込み画像もOCRで処理する。"""
    results = []

    # 埋め込み画像のOCR
    image_texts = _extract_images_from_xlsx(path)

    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    try:
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                continue

            headers = [str(c) if c is not None else "" for c in rows[0]]
            lines = [f"シート: {sheet_name}", f"カラム: {', '.join(headers)}"]

            for row in rows[1:]:
                cells = [str(c) if c is not None else "" for c in row]
                lines.append(" | ".join(cells))

            text = "\n".join(lines)
            results.append({
                "text": text,
                "metadata": {"source": path.name, "sheet": sheet_name},
            })
    finally:
        wb.close()

    # 画像テキストを追加（シートとの紐付けが困難なため別セクション）
    all_image_texts = image_texts.get("_all", [])
    if all_image_texts:
        results.append({
            "text": "\n\n".join(all_image_texts),
            "metadata": {"source": path.name, "sheet": "_images"},
        })

    return results
