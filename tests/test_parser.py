from __future__ import annotations

from pathlib import Path

from local_doc_mcp.parser import parse_file
from local_doc_mcp.parser.pdf import parse_pdf
from local_doc_mcp.parser.excel import parse_excel
from local_doc_mcp.parser.image import parse_image
from local_doc_mcp.parser.text import parse_text


class TestTextParser:
    def test_parse_text(self, fixtures_dir: Path):
        results = parse_text(fixtures_dir / "sample.txt")
        assert len(results) == 1
        assert "テスト用のテキストファイル" in results[0]["text"]
        assert results[0]["metadata"]["source"] == "sample.txt"

    def test_parse_empty_file(self, tmp_path: Path):
        empty = tmp_path / "empty.txt"
        empty.write_text("")
        results = parse_text(empty)
        assert results == []


class TestPdfParser:
    def test_parse_pdf(self, fixtures_dir: Path):
        results = parse_pdf(fixtures_dir / "sample.pdf")
        assert len(results) >= 1
        assert results[0]["metadata"]["source"] == "sample.pdf"
        assert results[0]["metadata"]["page"] == 1
        assert "Test PDF" in results[0]["text"]


class TestExcelParser:
    def test_parse_excel(self, fixtures_dir: Path):
        results = parse_excel(fixtures_dir / "sample.xlsx")
        assert len(results) >= 1
        result = results[0]
        assert result["metadata"]["source"] == "sample.xlsx"
        assert result["metadata"]["sheet"] == "テストシート"
        assert "ID" in result["text"]
        assert "名前" in result["text"]
        assert "項目A" in result["text"]


class TestImageParser:
    def test_parse_image(self, fixtures_dir: Path):
        results = parse_image(fixtures_dir / "sample.png")
        # OCRの結果は環境依存のため、最低限エラーなく動くことを確認
        assert isinstance(results, list)
        # テキストが取れた場合はメタ情報を検証
        if results:
            assert results[0]["metadata"]["source"] == "sample.png"
            assert isinstance(results[0]["text"], str)


class TestParseFileDispatch:
    def test_dispatch_txt(self, fixtures_dir: Path):
        results = parse_file(fixtures_dir / "sample.txt")
        assert len(results) >= 1

    def test_dispatch_pdf(self, fixtures_dir: Path):
        results = parse_file(fixtures_dir / "sample.pdf")
        assert len(results) >= 1

    def test_dispatch_xlsx(self, fixtures_dir: Path):
        results = parse_file(fixtures_dir / "sample.xlsx")
        assert len(results) >= 1

    def test_dispatch_png(self, fixtures_dir: Path):
        results = parse_file(fixtures_dir / "sample.png")
        assert isinstance(results, list)

    def test_unsupported_format(self, tmp_path: Path):
        unsupported = tmp_path / "test.xyz"
        unsupported.write_text("dummy")
        try:
            parse_file(unsupported)
            assert False, "ValueError が発生するべき"
        except ValueError as e:
            assert ".xyz" in str(e)
