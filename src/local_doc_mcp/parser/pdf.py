from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import pypdfium2 as pdfium

from local_doc_mcp.parser.ocr import ocr_from_image_bytes


def _collect_image_positions(page: pdfium.PdfPage) -> list[dict]:
    """ページ内の埋め込み画像の位置とバイナリを収集する。

    Returns:
        list[dict]: 各要素は {"top": float, "bottom": float, "image_base64": str,
                    "ocr_text": str}
                    top/bottom は PDF座標系（原点=左下、上が大きい）。
    """
    images: list[dict] = []
    for obj in page.get_objects():
        if obj.type != pdfium.raw.FPDF_PAGEOBJ_IMAGE:
            continue
        try:
            left, bottom, right, top = obj.get_bounds()
            img = obj.get_bitmap().to_pil()
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            image_b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        except Exception:
            continue

        # OCRは失敗しても画像自体は保持する
        ocr_text = ""
        try:
            ocr_text = ocr_from_image_bytes(buffer.getvalue())
        except Exception:
            pass

        images.append({
            "top": top,
            "bottom": bottom,
            "image_base64": image_b64,
            "ocr_text": ocr_text,
        })
    # 上から順（top が大きい順）にソート
    images.sort(key=lambda x: -x["top"])
    return images


def _split_text_by_images(
    textpage: pdfium.PdfTextPage,
    images: list[dict],
    page_height: float,
) -> list[dict]:
    """テキストを画像の位置で分割し、位置順のセグメントリストを返す。

    Returns:
        list[dict]: {"type": "text", "content": str} または
                    {"type": "image", "content": str, "ocr_text": str}
    """
    if not images:
        text = textpage.get_text_bounded().strip()
        if text:
            return [{"type": "text", "content": text}]
        return []

    char_count = textpage.count_chars()
    if char_count == 0:
        # テキストなし、画像のみ
        segments: list[dict] = []
        for img in images:
            segments.append({
                "type": "image",
                "content": img["image_base64"],
                "ocr_text": img["ocr_text"],
            })
        return segments

    # 各文字にY座標を付与して収集
    chars_with_y: list[tuple[int, float]] = []  # (char_index, top_y)
    for ci in range(char_count):
        try:
            _left, _bottom, _right, top = textpage.get_charbox(ci)
            chars_with_y.append((ci, top))
        except Exception:
            chars_with_y.append((ci, 0.0))

    # 画像の境界線（PDF座標系）を作成
    # 各画像の top / bottom でテキストを区切る
    boundaries: list[dict] = []
    for img in images:
        boundaries.append({"y": img["top"], "event": "image_start", "img": img})
        boundaries.append({"y": img["bottom"], "event": "image_end", "img": img})

    # セグメント構築: テキストを画像の位置で分割
    segments = []
    for img in images:
        img_top = img["top"]
        img_bottom = img["bottom"]

        # 画像より上のテキスト
        above_chars = [ci for ci, y in chars_with_y if y > img_top]
        # 画像より下のテキスト
        below_chars = [ci for ci, y in chars_with_y if y < img_bottom]
        # 画像と重なるテキスト（画像内テキスト）
        overlap_chars = [ci for ci, y in chars_with_y if img_bottom <= y <= img_top]

        # 初回のみ上部テキストを追加
        if not segments:
            if above_chars:
                text = _extract_chars(textpage, above_chars)
                if text:
                    segments.append({"type": "text", "content": text})

        # 画像セグメント
        segments.append({
            "type": "image",
            "content": img["image_base64"],
            "ocr_text": img["ocr_text"],
        })

    # 最後の画像より下のテキスト
    last_img_bottom = images[-1]["bottom"]
    below_chars = [ci for ci, y in chars_with_y if y < last_img_bottom]
    if below_chars:
        text = _extract_chars(textpage, below_chars)
        if text:
            segments.append({"type": "text", "content": text})

    # 画像間のテキストも処理（画像が複数ある場合）
    if len(images) > 1:
        new_segments = []
        for idx, img in enumerate(images):
            # この画像のセグメントを追加する前に、前の画像との間のテキストを追加
            if idx > 0:
                prev_bottom = images[idx - 1]["bottom"]
                curr_top = img["top"]
                between_chars = [
                    ci for ci, y in chars_with_y
                    if curr_top < y < prev_bottom
                ]
                if between_chars:
                    text = _extract_chars(textpage, between_chars)
                    if text:
                        new_segments.append({"type": "text", "content": text})
            # 対応する画像セグメントを探して追加
            for seg in segments:
                if seg["type"] == "image" and seg["content"] == img["image_base64"]:
                    new_segments.append(seg)
                    break

        # 上部テキストを先頭に
        if segments and segments[0]["type"] == "text":
            new_segments.insert(0, segments[0])
        # 下部テキストを末尾に
        if segments and segments[-1]["type"] == "text":
            new_segments.append(segments[-1])

        segments = new_segments

    return segments


def _extract_chars(textpage: pdfium.PdfTextPage, char_indices: list[int]) -> str:
    """指定された文字インデックスからテキストを抽出する。"""
    if not char_indices:
        return ""
    char_indices.sort()
    parts = []
    for ci in char_indices:
        parts.append(textpage.get_text_range(ci, 1))
    return "".join(parts).strip()


def parse_pdf(path: Path) -> list[dict]:
    """PDFをページ単位でテキスト・画像を位置順に抽出する。

    Returns:
        list[dict]: 各要素は以下のいずれか:
            - {"type": "text", "content": str, "metadata": {"source": str, "page": int}}
            - {"type": "image", "content": str (base64), "ocr_text": str,
               "metadata": {"source": str, "page": int}}
    """
    results: list[dict] = []
    pdf = pdfium.PdfDocument(str(path))
    try:
        for i, page in enumerate(pdf):
            page_height = page.get_height()

            # 画像オブジェクトの位置とデータを収集
            images = _collect_image_positions(page)

            # テキストを画像位置で分割
            textpage = page.get_textpage()
            segments = _split_text_by_images(textpage, images, page_height)
            textpage.close()

            page.close()

            metadata = {"source": path.name, "page": i + 1}
            for seg in segments:
                entry: dict = {
                    "type": seg["type"],
                    "content": seg["content"],
                    "metadata": dict(metadata),
                }
                if seg["type"] == "image":
                    entry["ocr_text"] = seg.get("ocr_text", "")
                results.append(entry)
    finally:
        pdf.close()
    return results
