from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session", autouse=True)
def generate_fixtures():
    """テスト用のサンプルファイルを生成する。"""
    FIXTURES_DIR.mkdir(exist_ok=True)
    _generate_pdf()
    _generate_excel()
    _generate_image()


def _generate_pdf():
    """pypdfium2 でテスト用PDFを生成する。"""
    import pypdfium2 as pdfium

    path = FIXTURES_DIR / "sample.pdf"
    if path.exists():
        return

    # 最小限のPDFをバイナリで作成
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length 44>>stream\n"
        b"BT /F1 12 Tf 100 700 Td (Test PDF Page 1) Tj ET\n"
        b"endstream endobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000266 00000 n \n"
        b"0000000360 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\n"
        b"startxref\n431\n%%EOF"
    )
    path.write_bytes(pdf_bytes)


def _generate_excel():
    """openpyxl でテスト用Excelを生成する。"""
    import openpyxl

    path = FIXTURES_DIR / "sample.xlsx"
    if path.exists():
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "テストシート"
    ws.append(["ID", "名前", "値"])
    ws.append([1, "項目A", 100])
    ws.append([2, "項目B", 200])
    wb.save(str(path))
    wb.close()


def _generate_image():
    """Pillow でテスト用画像を生成する。"""
    from PIL import Image, ImageDraw

    path = FIXTURES_DIR / "sample.png"
    if path.exists():
        return

    img = Image.new("RGB", (200, 50), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 15), "Hello OCR Test", fill="black")
    img.save(str(path))


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def tmp_db(tmp_path) -> Path:
    """テスト用の一時LanceDBディレクトリ。"""
    return tmp_path / "test_lancedb"
