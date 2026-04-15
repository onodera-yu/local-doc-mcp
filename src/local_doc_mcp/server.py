from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Image
from PIL import Image as PILImage

from local_doc_mcp.indexer import search
from local_doc_mcp.parser import parse_file


def _compress_image(image_b64: str, max_edge: int = 768, quality: int = 60) -> bytes:
    """Base64 PNG画像をリサイズ・JPEG圧縮してバイト列を返す。"""
    raw = base64.b64decode(image_b64)
    img = PILImage.open(BytesIO(raw))
    img.thumbnail((max_edge, max_edge))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()

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
def analyze_attachment(file_path: str, include_images: bool = False) -> list:
    """添付ファイルを解析し構造情報を返す。

    PDF / Excel / 画像 / テキストファイルに対応。
    ファイルの構造やテキスト内容を返却する。
    PDFの場合、テキストと画像がドキュメント内の配置順で返却される。

    include_images=Trueの場合、画像はMCPのImageContent型で返却され、
    LLMがビジョン入力として直接解釈できる。

    Args:
        file_path: 解析するファイルのパス
        include_images: Trueの場合、画像をMCP Image型で含める。
                        Falseの場合、画像の存在情報のみ返却する（デフォルト）。
    """
    path = Path(file_path)
    if not path.exists():
        return [{"error": f"ファイルが見つかりません: {file_path}"}]

    try:
        documents = parse_file(path)
        results: list = []
        # ファイル情報ヘッダー
        results.append({
            "file_type": path.suffix.lstrip("."),
            "file_name": path.name,
            "total_sections": len(documents),
        })

        for doc in documents:
            metadata = doc["metadata"]
            if doc.get("type") == "image":
                if include_images:
                    # MCP Image型で返却 → LLMがビジョン入力として解釈
                    compressed = _compress_image(doc["content"])
                    results.append(Image(data=compressed, format="jpeg"))
                else:
                    results.append({
                        "type": "image",
                        "description": "（画像: include_images=True で取得可能）",
                        "metadata": metadata,
                    })
                # OCRテキストがあればテキストとして追加
                if doc.get("ocr_text"):
                    results.append({
                        "type": "image_ocr",
                        "ocr_text": doc["ocr_text"][:2000],
                        "metadata": metadata,
                    })
            else:
                text = doc.get("content") or doc.get("text", "")
                results.append({
                    "type": "text",
                    "text": text[:2000],
                    "metadata": metadata,
                })

        return results
    except ValueError as e:
        return [{"error": str(e)}]


def main():
    mcp.run()


if __name__ == "__main__":
    main()
