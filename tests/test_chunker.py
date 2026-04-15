from __future__ import annotations

from local_doc_mcp.chunker import chunk_documents


class TestChunker:
    def test_short_text_no_split(self):
        docs = [{"text": "短いテキスト", "metadata": {"source": "a.txt"}}]
        chunks = chunk_documents(docs, chunk_size=800)
        assert len(chunks) == 1
        assert chunks[0]["text"] == "短いテキスト"
        assert chunks[0]["metadata"]["source"] == "a.txt"

    def test_long_text_splits(self):
        long_text = "あ" * 2000
        docs = [{"text": long_text, "metadata": {"source": "b.txt"}}]
        chunks = chunk_documents(docs, chunk_size=800, overlap=200)
        assert len(chunks) > 1
        # 各チャンクがchunk_size以下
        for chunk in chunks:
            assert len(chunk["text"]) <= 800

    def test_overlap(self):
        text = "A" * 1000
        docs = [{"text": text, "metadata": {"source": "c.txt"}}]
        chunks = chunk_documents(docs, chunk_size=600, overlap=100)
        assert len(chunks) == 2
        # 最初のチャンクの末尾と次のチャンクの先頭が重複
        assert chunks[0]["text"][-100:] == chunks[1]["text"][:100]

    def test_metadata_preserved(self):
        docs = [{"text": "x" * 2000, "metadata": {"source": "d.pdf", "page": 3}}]
        chunks = chunk_documents(docs, chunk_size=800)
        for chunk in chunks:
            assert chunk["metadata"]["source"] == "d.pdf"
            assert chunk["metadata"]["page"] == 3

    def test_multiple_documents(self):
        docs = [
            {"text": "ドキュメント1", "metadata": {"source": "a.txt"}},
            {"text": "ドキュメント2", "metadata": {"source": "b.txt"}},
        ]
        chunks = chunk_documents(docs, chunk_size=800)
        assert len(chunks) == 2
        assert chunks[0]["metadata"]["source"] == "a.txt"
        assert chunks[1]["metadata"]["source"] == "b.txt"

    def test_empty_input(self):
        chunks = chunk_documents([])
        assert chunks == []
