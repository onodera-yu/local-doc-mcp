from __future__ import annotations

from pathlib import Path

from local_doc_mcp.indexer import build_index, search


class TestIndexer:
    def _sample_chunks(self) -> list[dict]:
        return [
            {
                "text": "監視IDは一意である必要があります。重複は許可されません。",
                "metadata": {"source": "manual.pdf", "page": 5, "sheet": ""},
            },
            {
                "text": "アラート通知はメールとSlackの両方に送信されます。",
                "metadata": {"source": "manual.pdf", "page": 10, "sheet": ""},
            },
            {
                "text": "設定ファイルはYAML形式で記述してください。",
                "metadata": {"source": "guide.txt", "page": 0, "sheet": ""},
            },
        ]

    def test_build_index(self, tmp_db: Path):
        chunks = self._sample_chunks()
        count = build_index(tmp_db, chunks)
        assert count == 3

    def test_build_index_empty(self, tmp_db: Path):
        count = build_index(tmp_db, [])
        assert count == 0

    def test_search(self, tmp_db: Path):
        chunks = self._sample_chunks()
        build_index(tmp_db, chunks)

        results = search(tmp_db, "監視IDについて教えて", top_k=2)
        assert len(results) <= 2
        assert all("text" in r for r in results)
        assert all("source" in r for r in results)

    def test_search_returns_relevant(self, tmp_db: Path):
        chunks = self._sample_chunks()
        build_index(tmp_db, chunks)

        results = search(tmp_db, "アラート通知", top_k=1)
        assert len(results) == 1
        assert "アラート" in results[0]["text"] or "通知" in results[0]["text"]

    def test_search_empty_db(self, tmp_db: Path):
        results = search(tmp_db, "何か検索", top_k=5)
        assert results == []

    def test_rebuild_index(self, tmp_db: Path):
        chunks = self._sample_chunks()
        build_index(tmp_db, chunks)

        new_chunks = [
            {
                "text": "新しいドキュメントの内容です。",
                "metadata": {"source": "new.txt", "page": 0, "sheet": ""},
            },
        ]
        count = build_index(tmp_db, new_chunks)
        assert count == 1

        results = search(tmp_db, "新しいドキュメント", top_k=5)
        # 旧データは消えて新しいデータだけ
        assert all(r["source"] == "new.txt" for r in results)
