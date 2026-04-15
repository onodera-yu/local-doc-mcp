# local-doc-mcp

ローカルPC内のドキュメントをLLMから検索・参照できるMCPサーバー。

外部APIへのデータ送信を一切行わず、Embedding生成からベクトル検索まで全てローカルで完結します。

## 特徴

- **完全ローカル** - ドキュメントデータが外部に送信されない
- **クロスプラットフォーム** - Mac / Windows / Linux で動作
- **pip だけで完結** - OS側の追加インストール不要（tesseract等の別途導入は不要）
- **複数ファイル形式対応** - PDF / Excel / 画像 / テキスト（PDF・Excel内の埋め込み画像もOCR対応）
- **日本語対応** - 多言語Embeddingモデルにより日本語ドキュメントを高精度で検索

## システム構成

```
ユーザー
  ↓
LLM（Claude Desktop / Kiro / Claude Code 等）
  ↓  MCP Protocol
MCP Server（local-doc-mcp）
  ↓
RAG検索（LanceDB + fastembed）
  ↓
ナレッジドキュメント（ローカルファイル）
```

## 必要環境

- Python 3.11 以上
- [uv](https://docs.astral.sh/uv/)（パッケージマネージャ）

## クイックスタート

```bash
# 1. リポジトリをクローン
git clone https://github.com/<your-org>/local-doc-mcp.git
cd local-doc-mcp

# 2. 依存パッケージをインストール
uv sync

# 3. knowledge/ にドキュメントを配置
cp /path/to/your/documents/* knowledge/

# 4. インデックスを構築
uv run build-index

# 5. MCPサーバーを起動（動作確認）
uv run local-doc-mcp
```

## MCP クライアントへの接続

### Claude Desktop

`claude_desktop_config.json` に以下を追加:

```json
{
  "mcpServers": {
    "local-doc-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/local-doc-mcp", "run", "local-doc-mcp"]
    }
  }
}
```

### Claude Code

`claude_code_config.json` または `.mcp.json` に以下を追加:

```json
{
  "mcpServers": {
    "local-doc-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/local-doc-mcp", "run", "local-doc-mcp"]
    }
  }
}
```

### Kiro

Kiro の MCP設定画面から、上記と同様のコマンドを登録してください。

## MCPツール

### `search_docs(query: str, top_k: int = 5)`

ナレッジドキュメントをベクトル検索し、クエリに関連するチャンクを返します。

**パラメータ:**

| 名前 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `query` | `str` | (必須) | 検索クエリ（日本語可） |
| `top_k` | `int` | `5` | 返却する上位件数 |

**戻り値の例:**

```json
[
  {
    "text": "監視IDは一意である必要があります",
    "source": "monitoring_manual.pdf",
    "page": 12,
    "sheet": null
  }
]
```

### `analyze_attachment(file_path: str, include_images: bool = False)`

ファイルを解析し、構造情報を返します。インデックスに登録されていないファイルも解析可能です。
PDFの場合、テキストと埋め込み画像がドキュメント内の配置順序を保持して返却されます。

**パラメータ:**

| 名前 | 型 | デフォルト | 説明 |
|---|---|---|---|
| `file_path` | `str` | (必須) | 解析するファイルのパス |
| `include_images` | `bool` | `False` | `True` の場合、画像のBase64データを含める。`False` の場合、画像の存在情報のみ返却する |

**戻り値の例（Excel等テキストのみ）:**

```json
{
  "file_type": "xlsx",
  "file_name": "monitoring_settings.xlsx",
  "sections": [
    {
      "type": "text",
      "text": "シート: 監視設定\nカラム: 監視ID, 監視対象, 閾値, 通知先\n...",
      "metadata": { "source": "monitoring_settings.xlsx", "sheet": "監視設定" }
    }
  ]
}
```

**戻り値の例（PDF・テキストと画像の混在、`include_images=False`）:**

```json
{
  "file_type": "pdf",
  "file_name": "report.pdf",
  "sections": [
    {
      "type": "text",
      "text": "売上レポート 2024年度...",
      "metadata": { "source": "report.pdf", "page": 1 }
    },
    {
      "type": "image",
      "description": "（画像: include_images=True で取得可能）",
      "ocr_text": "売上推移グラフ 1月 2月...",
      "metadata": { "source": "report.pdf", "page": 1 }
    },
    {
      "type": "text",
      "text": "上記グラフの通り、Q3に売上が急伸...",
      "metadata": { "source": "report.pdf", "page": 1 }
    }
  ]
}
```

**戻り値の例（PDF・`include_images=True`）:**

```json
{
  "file_type": "pdf",
  "file_name": "report.pdf",
  "sections": [
    {
      "type": "text",
      "text": "売上レポート 2024年度...",
      "metadata": { "source": "report.pdf", "page": 1 }
    },
    {
      "type": "image",
      "image_base64": "iVBORw0KGgo...",
      "mime_type": "image/png",
      "ocr_text": "売上推移グラフ 1月 2月...",
      "metadata": { "source": "report.pdf", "page": 1 }
    },
    {
      "type": "text",
      "text": "上記グラフの通り、Q3に売上が急伸...",
      "metadata": { "source": "report.pdf", "page": 1 }
    }
  ]
}
```

## 対応ファイル形式

| 形式 | 拡張子 | 処理内容 |
|---|---|---|
| PDF | `.pdf` | テキスト抽出 + 埋め込み画像のBase64返却・OCR（配置順序を保持） |
| Excel | `.xlsx`, `.xls` | シート構造の文章化 + 埋め込み画像のOCR |
| 画像 | `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.tif` | OCRによるテキスト抽出 |
| テキスト | `.txt`, `.md`, `.csv`, `.log` | そのまま読み込み |

## インデックス構築オプション

```bash
uv run build-index [OPTIONS]
```

| オプション | デフォルト | 説明 |
|---|---|---|
| `--docs-dir` | `knowledge/` | ドキュメントディレクトリのパス |
| `--db-dir` | `lancedb_data/` | LanceDB データディレクトリのパス |
| `--chunk-size` | `800` | チャンクサイズ（文字数） |
| `--overlap` | `200` | チャンク間のオーバーラップ（文字数） |

ドキュメントを更新した場合は、再度 `build-index` を実行してください。

## 技術スタック

| 項目 | ライブラリ | ライセンス |
|---|---|---|
| MCPサーバー | [mcp (FastMCP)](https://github.com/modelcontextprotocol/python-sdk) | MIT |
| ベクトルDB | [LanceDB](https://github.com/lancedb/lancedb) | Apache 2.0 |
| Embedding | [fastembed](https://github.com/qdrant/fastembed) | Apache 2.0 |
| Embeddingモデル | [intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small) | MIT |
| PDF解析 | [pypdfium2](https://github.com/nicegui-dev/pypdfium2) | Apache 2.0 / BSD 3 |
| Excel解析 | [openpyxl](https://openpyxl.readthedocs.io/) | MIT |
| 画像OCR | [RapidOCR](https://github.com/RapidAI/RapidOCR) | Apache 2.0 |
| データ処理 | [pandas](https://pandas.pydata.org/) | BSD 3 |

全ライブラリが非コピーレフトライセンス（MIT / Apache 2.0 / BSD）です。

技術選定の詳細な理由は [docs/design.md](docs/design.md) を参照してください。

## ディレクトリ構成

```
local-doc-mcp/
├── pyproject.toml          # 依存管理・プロジェクト設定
├── README.md
├── LICENSE
├── docs/
│   └── design.md           # 設計ドキュメント（技術選定理由等）
├── src/
│   └── local_doc_mcp/
│       ├── server.py        # MCPサーバー本体
│       ├── indexer.py       # LanceDB インデックス構築・検索
│       ├── embedder.py      # Embedding 生成（fastembed）
│       ├── chunker.py       # テキストのチャンク分割
│       ├── parser/
│       │   ├── __init__.py  # ファイル形式に応じた振り分け
│       │   ├── ocr.py       # OCR共有モジュール
│       │   ├── pdf.py       # PDF解析（テキスト + 画像OCR）
│       │   ├── excel.py     # Excel解析（シート構造 + 画像OCR）
│       │   ├── image.py     # 画像OCR
│       │   └── text.py      # テキストファイル読み込み
│       └── scripts/
│           └── build_index.py  # インデックス構築CLI
├── knowledge/              # ナレッジドキュメント置き場
└── lancedb_data/           # ベクトルDBデータ（自動生成・gitignore対象）
```

## ライセンス

[MIT License](LICENSE)
