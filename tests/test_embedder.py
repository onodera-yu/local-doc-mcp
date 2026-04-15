from __future__ import annotations

from local_doc_mcp.embedder import embed_texts


class TestEmbedder:
    def test_single_text(self):
        vectors = embed_texts(["テスト文章"])
        assert len(vectors) == 1
        assert len(vectors[0]) > 0
        assert all(isinstance(v, float) for v in vectors[0])

    def test_multiple_texts(self):
        texts = ["文章A", "文章B", "文章C"]
        vectors = embed_texts(texts)
        assert len(vectors) == 3
        # 全てのベクトルが同じ次元数
        dim = len(vectors[0])
        assert all(len(v) == dim for v in vectors)

    def test_consistent_dimension(self):
        v1 = embed_texts(["短い"])
        v2 = embed_texts(["これはもう少し長い文章です。テストのために書いています。"])
        assert len(v1[0]) == len(v2[0])
