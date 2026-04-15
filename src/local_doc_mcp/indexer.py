from __future__ import annotations

from pathlib import Path

import lancedb
import pyarrow as pa

from local_doc_mcp.embedder import embed_texts

TABLE_NAME = "documents"


def get_db(db_path: str | Path) -> lancedb.DBConnection:
    """LanceDB の接続を返す。"""
    return lancedb.connect(str(db_path))


def _table_exists(db: lancedb.DBConnection, name: str) -> bool:
    """テーブルが存在するか確認する。"""
    return name in db.list_tables().tables


def build_index(db_path: str | Path, chunks: list[dict]) -> int:
    """チャンクリストからインデックスを構築する。

    既存テーブルがあれば削除して再作成する。

    Returns:
        登録されたチャンク数。
    """
    if not chunks:
        return 0

    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts)

    records = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        records.append({
            "id": i,
            "text": chunk["text"],
            "source": chunk["metadata"].get("source", ""),
            "page": chunk["metadata"].get("page", 0),
            "sheet": chunk["metadata"].get("sheet", ""),
            "vector": vector,
        })

    db = get_db(db_path)

    if _table_exists(db, TABLE_NAME):
        db.drop_table(TABLE_NAME)

    db.create_table(TABLE_NAME, data=records)
    return len(records)


def search(db_path: str | Path, query: str, top_k: int = 5) -> list[dict]:
    """クエリに類似するドキュメントを検索する。"""
    db = get_db(db_path)

    if not _table_exists(db, TABLE_NAME):
        return []

    table = db.open_table(TABLE_NAME)
    query_vector = embed_texts([query])[0]

    results = (
        table.search(query_vector)
        .limit(top_k)
        .to_pandas()
    )

    return [
        {
            "text": row["text"],
            "source": row["source"],
            "page": int(row["page"]) if row["page"] else None,
            "sheet": row["sheet"] if row["sheet"] else None,
        }
        for _, row in results.iterrows()
    ]
