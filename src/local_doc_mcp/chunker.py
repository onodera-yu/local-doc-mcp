from __future__ import annotations


def chunk_documents(
    documents: list[dict],
    chunk_size: int = 800,
    overlap: int = 200,
) -> list[dict]:
    """ドキュメントをチャンクに分割する。

    Args:
        documents: parse_file() の戻り値。各要素は {"text", "metadata"}。
        chunk_size: 1チャンクの最大文字数。
        overlap: チャンク間のオーバーラップ文字数。

    Returns:
        チャンクのリスト。各要素は {"text", "metadata"}。
    """
    chunks: list[dict] = []
    for doc in documents:
        text = doc["text"]
        metadata = doc["metadata"]

        if len(text) <= chunk_size:
            chunks.append({"text": text, "metadata": metadata})
            continue

        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            chunks.append({"text": chunk_text, "metadata": metadata.copy()})
            start += chunk_size - overlap

    return chunks
