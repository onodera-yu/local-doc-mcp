# local-doc-mcp

ローカルPC内のドキュメントをLLMから検索・参照できるMCPサーバー。

## 技術スタック

| 項目 | ライブラリ | 備考 |
|---|---|---|
| MCPサーバー | mcp[cli] (FastMCP) | 公式SDK |
| Embedding | fastembed | ONNX基盤、multilingual-e5-small |
| PDF解析 | pypdfium2 | Chromium PDFiumバインディング。テキストと画像を座標ベースで配置順に抽出 |
| Excel解析 | openpyxl | pandas併用 |
| 画像OCR | rapidocr-onnxruntime | pip完結、OS依存なし |
| ベクトルDB | lancedb | Apache Arrow基盤、ファイルベース |

## 設計方針

- 完全ローカル完結（外部APIへのデータ送信なし）
- クロスプラットフォーム（Mac / Windows / Linux）
- 全ライブラリ非コピーレフト（MIT / Apache 2.0 / BSD）
- パッケージマネージャは uv を使用

## ディレクトリ構成

- `src/local_doc_mcp/` - メインパッケージ
- `src/local_doc_mcp/parser/` - ファイル形式別パーサー
- `src/local_doc_mcp/scripts/` - CLIスクリプト
- `knowledge/` - ナレッジドキュメント置き場
- `lancedb_data/` - ベクトルDBデータ（自動生成）
- `docs/` - 設計ドキュメント

## コマンド

```bash
uv run build-index          # インデックス構築
uv run local-doc-mcp        # MCPサーバー起動
```
