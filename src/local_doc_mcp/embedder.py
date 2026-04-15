from __future__ import annotations

from fastembed import TextEmbedding

MODEL_NAME = "intfloat/multilingual-e5-large"

_model: TextEmbedding | None = None


def get_model() -> TextEmbedding:
    """Embeddingモデルのシングルトンを返す。"""
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """テキストリストをEmbeddingベクトルに変換する。"""
    model = get_model()
    # fastembed は generator を返すので list 化
    return list(model.embed(texts))
