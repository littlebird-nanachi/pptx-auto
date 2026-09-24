# Phase 1 設計

ロゴは案件やテーマごとに用意し、`themes/<theme>/logo.png` または `assets/logo.png` に配置する。

## 技術・構成
Python 3.12+ / Jinja2 (自動エスケープ) / JSON Schema / Playwright Chromium / Pillow / python-pptx。
JSON → Schema検証 → Theme解決 → 共通SlideShell + Layout → HTML → DOM QA → PNG → PPTX。
LLMはPhase 3で追加する。Phase 1ではJSONを入力とし、架空のAI生成機能は設けない。

- `src/pptxgen/schemas.py`: Slide JSON Schema
- `src/pptxgen/theme.py`: Themeとロゴ解決
- `src/pptxgen/shell.html`: 全Layout共通のHeader、Title、Lead、Footer
- `src/pptxgen/layouts/`: 本文のみの3テンプレート
- `src/pptxgen/renderer.py`: HTML生成
- `src/pptxgen/qa.js`: Chromium内での幾何学検査
- `src/pptxgen/pipeline.py`: PNGとPPTX生成、QAレポート
- `styles/`: 共通Design Tokensとレイアウト

## JSON Schema
presentation: title, audience, purpose / slides: slide_number, layout, title, lead。
Layout固有項目: titleはsubtitle、comparison_2colはleft/rightのheading/items、cards_3colは3個のheading/items。
未知の項目・Layout、不正な型、空文字は拒否。ページ番号は1からの連番。

## ロゴ
Theme選択は安全なディレクトリ名のみ。`themes/<theme>/logo.png` が存在すれば優先し、存在しない場合に `assets/logo.png` を使う。壊れたTheme画像はエラー（黙ってFallbackしない）。画像はPillowで実際にデコードし、HTMLへData URIで埋め込む。高さ48px、幅auto。実画像比からSafe Areaを計算し、タイトル・Leadの幅を制限する。本文開始位置もロゴ下端＋余白より下にする。横長すぎるロゴ等はQAエラーにする。

## QAと生成の停止
各ページの画像読み込み、表示数、位置、縦横比、タイトル/本文との重なり、文字の最小サイズ、要素/文字のはみ出しを検査。PNGサイズとPPTX枚数を検証。失敗は `qa_report.json` に保存して非ゼロ終了し、新規PPTXを公開しない。作業は一時ディレクトリで行い、成功時のみ成果物を置き換える。既存出力は失敗時に保持されるため、QAレポートを必ず確認する。

## Phase 1 手順
1. Schema・Theme・共通Shellと3 Layoutを実装
2. ChromiumによるQAとPNG生成
3. 全面PNGのPPTX生成、プレビューHTML
4. 長いタイトル、Theme優先/Fallback、壊れた/欠損ロゴ、重なり、16:9/4:3をテスト
5. 汎用入力データを使って複数レイアウトを実際に生成・目視検証

Phase 2: Layout追加 / Phase 3: Planner・LLM / Phase 4: 自動修正・再試行 / Phase 5: Preview編集UI。
現段階では内容を自動で削ったり縮小せず、QA指摘を受けてJSONやThemeを修正して再実行する。
