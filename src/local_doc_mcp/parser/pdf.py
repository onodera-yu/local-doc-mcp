from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pypdfium2 as pdfium

from local_doc_mcp.parser.ocr import ocr_from_image_bytes


def _extract_images_text(page: pdfium.PdfPage) -> str:
    """ページ内の埋め込み画像をOCRでテキスト化する。"""
    texts = []
    for obj in page.get_objects():
        if obj.type == pdfium.raw.FPDF_PAGEOBJ_IMAGE:
            try:
                img = obj.get_bitmap().to_pil()
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                text = ocr_from_image_bytes(buffer.getvalue())
                if text:
                    texts.append(text)
            except Exception:
                continue
    return "\n".join(texts)


def parse_pdf(path: Path) -> list[dict]:
    """PDFをページ単位でテキスト抽出する。埋め込み画像もOCRで処理する。"""
    results = []
    pdf = pdfium.PdfDocument(str(path))
    try:
        for i, page in enumerate(pdf):
            # テキストレイヤーの抽出
            textpage = page.get_textpage()
            text = textpage.get_text_bounded().strip()
            textpage.close()

            # 埋め込み画像のOCR
            image_text = _extract_images_text(page)

            page.close()

            parts = [p for p in [text, image_text] if p]
            combined = "\n\n".join(parts)

            if combined:
                results.append({
                    "text": combined,
                    "metadata": {"source": path.name, "page": i + 1},
                })
    finally:
        pdf.close()
    return results
