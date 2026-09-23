# auto-pptxe

HTML/CSSからレビュー用PNGとPowerPoint（PPTX）を生成する汎用テンプレート。

案件固有の入力資料や成果物は含めず、生成基盤・レイアウト・テーマ・QA・サンプルだけを管理する。

JSON → Jinja2 HTML/CSS → Chromium PNG → Humanレビュー → 承認後に全面画像のPPTX。
`title` / `comparison_2col` / `cards_3col` に対応。設計は [docs/design.md](docs/design.md)。

## 実行

Python 3.12+ を使用します。

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
# 1. HTML/PNG/プレビューを生成（この段階ではPPTXを作らない）
PYTHONPATH=src .venv/bin/python -m pptxgen --input examples/phase1.json --output output --ratio 4:3

# 2. output/preview.html を人が確認し、承認後に実行
PYTHONPATH=src .venv/bin/python -m pptxgen --output output --approve
```

既存Chromeを使う場合は `PPTXGEN_CHROMIUM` にChrome実行ファイルの絶対パスを指定します。
`--ratio 4:3` で1440×1080、通常は1920×1080。`--theme client_a` でThemeを選択。
初回の生成結果は `html/`、`images/`、`preview.html`、`qa_report.json`、`review_manifest.json`。
QA通過後も人の承認までは `presentation.pptx` を生成しません。`--approve` は既存のレビュー済みHTML/PNGを再生成せず、そのままPPTXへパッケージします。
プレビューの画像をクリックすると原寸で確認できます。PPTX内の内容は画像であり直接編集できません。

## 作業の進め方

基本的には、次のサイクルで1枚ずつ内容と見た目を固めます。

1. `examples/phase1.json` をコピーし、ページの文章・データ・使用する `layout` を定義する。
2. 生成コマンドを実行し、`output/preview.html` と生成されたPNGを確認する。
3. 文章の長さ、余白、整列、ロゴ位置、ページ間の統一感を人がレビューする。
4. 修正があれば JSON、レイアウトHTML、CSS、テーマのいずれかを直して再生成する。
5. QAが通ったレビュー済みの出力に対して、承認後 `--approve` を実行する。
6. `output/presentation.pptx` を納品物として確認し、コード変更とサンプル入力をコミットする。

```text
入力JSON
   ↓
レイアウト選択・文章調整
   ↓
HTML / CSS / PNG 生成
   ↓
preview.html を人がレビュー
   ├─ 修正あり → JSON / レイアウト / CSS に戻る
   └─ 承認    → --approve
                  ↓
              presentation.pptx
```

案件固有のJSONや生成物をリポジトリに残す必要がない場合は、`examples/` をサンプルとして使い、実案件の入力・出力は別の作業ディレクトリで管理します。

## 共通ロゴ

`src/pptxgen/shell.html` だけがロゴを描画します。各Layoutは本文のみを持ちます。
優先順位は `themes/<theme>/logo.png` → `assets/logo.png`。
Themeロゴが欠損ならFallback、破損・読み込み失敗ならエラー。画像をHTMLに埋め込むため出力の移動でもリンク切れしません。

`styles/tokens.css` の既定値: `--logo-top:40px`、`--logo-right:64px`、`--logo-height:48px`。
幅は `auto`、Safe Areaは実画像の縦横比と高さから計算し、32pxの余白を加えます。
タイトルとリードはSafe Areaを避けて折り返します。本文は共通ヘッダー下に配置します。
画像を引き伸ばしたり、本文をoverflow:hiddenで隠すことはありません。

任意の `themes/<theme>/theme.json`:

```json
{"tokens":{"logo-top":40,"logo-right":64,"logo-height":48,"logo-gap":32},"footer":"Client name"}
```

数値はpx。設定可能なtoken一覧は `theme.py` を参照。最小フォントサイズは12px（96dpi換算9pt）。
ロゴ位置・寸法がキャンバス内に収まらない場合はQAエラー。極端に長いタイトルや本文も修正対象として報告します。

## QA・テスト

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

ロゴの読み込み、全ページに1個、表示状態、右上座標、アスペクト比、タイトル/本文との重なりをChromiumの実測で検証。
Schema、ページ番号、文字重複・はみ出し、最小フォント、PNG寸法、PPTX枚数も検査します。
エラーは `qa_report.json` に保存して非ゼロ終了。既存PPTXがある場合は失敗しても前回のファイルが残るため、最新QAの `generated` を確認してください。

Phase 2以降の20 Layout・LLMストーリー生成・自動修正・編集UIは未実装です。
