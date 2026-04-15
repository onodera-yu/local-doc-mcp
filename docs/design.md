# 設計ドキュメント

このドキュメントでは、local-doc-mcp の設計判断とその理由を記録する。

## 設計原則

| 原則 | 説明 |
|---|---|
| 完全ローカル | ドキュメントデータを外部APIに送信しない。Embedding生成も推論もローカルで完結する |
| クロスプラットフォーム | Mac / Windows / Linux で同一手順で動作する。OS側の追加インストールを要求しない |
| 非コピーレフト | 全ての依存ライブラリが MIT / Apache 2.0 / BSD のいずれか |
| 軽量・高速 | 同等の機能を持つライブラリが複数ある場合、より高速なものを選定する |

---

## 技術選定の理由

### MCPサーバー: mcp[cli] (FastMCP)

**採用理由:**
- FastMCP の作者が公式 MCP Python SDK にコードを寄贈済み
- `from mcp.server.fastmcp import FastMCP` でそのまま利用可能
- 別パッケージとしての `fastmcp` は不要

**不採用:**
- `fastmcp`（旧スタンドアロン版）: 公式SDKに統合されたため不要

### ベクトルDB: LanceDB

**採用理由:**
- Apache Arrow 基盤で検索・I/O が高速
- ファイルベースで完結し、サーバープロセスが不要
- 小〜中規模（数千〜数万チャンク）に最適

**不採用:**
- ChromaDB: サーバープロセスが必要になりつつある。依存が重い
- FAISS: 高速だが、メタデータ管理を自前実装する必要がある

### Embedding: fastembed

**採用理由:**
- ONNX Runtime 基盤で PyTorch 不要（環境サイズが数GB軽くなる）
- sentence-transformers と同等精度で 2-3倍高速
- `intfloat/multilingual-e5-small` をサポートしており日本語対応

**不採用:**
- sentence-transformers: PyTorch ごとインストールされるため環境が重い（数GB）

### Embeddingモデル: intfloat/multilingual-e5-small

**採用理由:**
- 多言語対応（日本語ドキュメントの検索精度が高い）
- 軽量で推論速度が速い
- MIT ライセンス

**検討候補:**
- `intfloat/multilingual-e5-base`: より高精度だがモデルサイズが大きい。精度が不足する場合に切り替えを検討

### PDF解析: pypdfium2

**採用理由:**
- Google Chromium の PDFium エンジンの Python バインディング
- C基盤のため Pure Python 実装（pdfplumber等）より数倍高速
- Apache 2.0 / BSD 3 のデュアルライセンス

**不採用:**
- PyMuPDF (fitz): 高機能だが AGPL ライセンス（コピーレフト）
- pdfplumber: Pure Python で安全だが速度が遅い

### 画像OCR: rapidocr-onnxruntime

**採用理由:**
- pip だけでインストール完結（OS側にバイナリ不要）
- ONNX Runtime 基盤で高速
- 日本語を含む多言語対応
- Mac / Windows / Linux で同一手順で動作

**不採用:**
- tesseract (pytesseract): OS側に `tesseract-ocr` バイナリのインストールが必要。Windows での導入が煩雑
- EasyOCR: PyTorch 依存で環境が重い

---

## ドキュメント処理フロー

### 前処理パイプライン

```
ドキュメントファイル
  ↓ parser（形式別）
セクションリスト [{ type, content, metadata }]
  ※ PDFの場合 type は "text" または "image" で、配置順序を保持
  ↓ chunker
チャンクリスト [{ text, metadata }]
  ↓ embedder（fastembed）
ベクトル付きチャンク
  ↓ indexer
LanceDB に保存
```

### ファイル形式別の処理

| 形式 | テキスト抽出 | 画像処理 | メタ情報 |
|---|---|---|---|
| PDF | pypdfium2 でページ単位抽出 | ページ内の埋め込み画像をBase64で返却 + OCR。テキストと画像は座標ベースでドキュメント内の配置順序を保持 | source, page |
| Excel | openpyxl でシート構造を文章化 | xl/media/ 内の画像をOCR | source, sheet |
| 画像 | - | rapidocr でOCR | source |
| テキスト | そのまま読み込み | - | source |

### チャンク化

| 項目 | デフォルト値 | 説明 |
|---|---|---|
| チャンクサイズ | 800文字 | 1チャンクの最大文字数 |
| オーバーラップ | 200文字 | チャンク間で重複させる文字数。文脈の切断を防ぐ |

### 検索フロー

```
検索クエリ
  ↓ embedder（fastembed）
クエリベクトル
  ↓ LanceDB ベクトル検索
上位 N 件のチャンク（text + metadata）
  ↓
LLM に提供
```

---

## MCPツール設計

### search_docs

- クエリをEmbedding化し、LanceDB でベクトル類似検索を行う
- 上位 N 件のチャンクを text / source / page / sheet 付きで返却
- LLM はこの結果を根拠として回答を生成し、引用元を明示する

### analyze_attachment

- インデックスに登録されていないファイルもその場で解析可能
- ファイル形式を自動判定し、対応するパーサーで構造情報を返却
- PDFの場合、テキストと埋め込み画像を座標ベースでドキュメント内の配置順序を保持して返却する。`include_images=True` を指定した場合、画像はBase64エンコードしたPNGとして返却され、LLMがマルチモーダルに解釈可能。デフォルト（`False`）では画像の存在情報のみ返却し、レスポンスサイズを抑える
- LLM はこの結果をもとにファイルの内容を理解・照合する

---

## LLM回答ルール（推奨システムプロンプト）

MCPクライアント側で以下のルールを設定することを推奨する:

- 必ず `search_docs` の検索結果を根拠として回答すること
- 引用元（ファイル名・ページ番号）を明記すること
- 検索結果に該当情報がない場合は推測せず「情報が見つかりませんでした」と回答すること

推奨回答フォーマット:

```
（回答本文）

引用:
- ファイル名 p.XX
- ファイル名 p.XX
```

---

## 制約事項・既知の制限

- Excel内の埋め込み画像はシートとの紐付けが技術的に困難なため、`_images` という別セクションとしてまとめている
- OCRの精度は画像の解像度に依存する
- Embeddingモデルは初回起動時に自動ダウンロードされる（初回のみネットワーク接続が必要）
- スキャンPDF（テキストレイヤーなし・画像のみ）は、ページ全体を画像としてOCRする処理は未実装（埋め込み画像オブジェクトとして検出できるもののみ対応）

---

## 今後の拡張候補

- ドキュメント更新時の差分インデックス更新
- スキャンPDF のページ全体OCR対応
- 監査ログ保存
- 回答品質評価の仕組み
