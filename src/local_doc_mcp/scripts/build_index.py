"""ナレッジドキュメントのインデックスを構築するスクリプト。

Usage:
    uv run build-index [--docs-dir <path>] [--db-dir <path>]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from local_doc_mcp.chunker import chunk_documents
from local_doc_mcp.indexer import build_index
from local_doc_mcp.parser import parse_file


DEFAULT_DOCS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "knowledge"
DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "lancedb_data"


def main():
    parser = argparse.ArgumentParser(description="ナレッジドキュメントのインデックスを構築")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=DEFAULT_DOCS_DIR,
        help="ドキュメントディレクトリのパス",
    )
    parser.add_argument(
        "--db-dir",
        type=Path,
        default=DEFAULT_DB_DIR,
        help="LanceDB データディレクトリのパス",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="チャンクサイズ（文字数）",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=200,
        help="チャンク間のオーバーラップ（文字数）",
    )
    args = parser.parse_args()

    docs_dir: Path = args.docs_dir
    if not docs_dir.exists():
        print(f"エラー: ドキュメントディレクトリが見つかりません: {docs_dir}", file=sys.stderr)
        sys.exit(1)

    files = [f for f in docs_dir.rglob("*") if f.is_file() and not f.name.startswith(".")]
    if not files:
        print(f"エラー: ドキュメントが見つかりません: {docs_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"対象ファイル: {len(files)} 件")

    all_documents: list[dict] = []
    for f in sorted(files):
        try:
            docs = parse_file(f)
            all_documents.extend(docs)
            print(f"  解析完了: {f.name} ({len(docs)} セクション)")
        except ValueError as e:
            print(f"  スキップ: {e}")

    print(f"チャンク化中 (size={args.chunk_size}, overlap={args.overlap}) ...")
    chunks = chunk_documents(all_documents, chunk_size=args.chunk_size, overlap=args.overlap)
    print(f"  チャンク数: {len(chunks)}")

    print("インデックス構築中 ...")
    count = build_index(args.db_dir, chunks)
    print(f"完了: {count} チャンクを登録しました -> {args.db_dir}")


if __name__ == "__main__":
    main()
