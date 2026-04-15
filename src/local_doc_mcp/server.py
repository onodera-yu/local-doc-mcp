from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from local_doc_mcp.indexer import search
from local_doc_mcp.parser import parse_file

DB_PATH = Path(__file__).resolve().parent.parent.parent / "lancedb_data"

mcp = FastMCP("local-doc-mcp")


@mcp.tool()
def search_docs(query: str, top_k: int = 5) -> list[dict]:
    """ローカルドキュメントをベクトル検索する。

    クエリに関連するドキュメントチャンクを返す。
    各結果には text, source, page, sheet を含む。

    Args:
        query: 検索クエリ（日本語可）
        top_k: 返却する上位件数（デフォルト5）
    """
    return search(DB_PATH, query, top_k=top_k)


@mcp.tool()
def analyze_attachment(file_path: str) -> dict:
    """添付ファイルを解析し構造情報を返す。

    PDF / Excel / 画像 / テキストファイルに対応。
    ファイルの構造やテキスト内容を返却する。

    Args:
        file_path: 解析するファイルのパス
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"ファイルが見つかりません: {file_path}"}

    try:
        documents = parse_file(path)
        return {
            "file_type": path.suffix.lstrip("."),
            "file_name": path.name,
            "sections": [
                {
                    "text": doc["text"][:2000],
                    "metadata": doc["metadata"],
                }
                for doc in documents
            ],
        }
    except ValueError as e:
        return {"error": str(e)}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
