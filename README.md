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
PYTHONPATH=src .venv/bin/python -m pptxgen --input path/to/input.json --output output --ratio 4:3

# 2. output/preview.html を人が確認し、承認後に実行
PYTHONPATH=src .venv/bin/python -m pptxgen --output output --approve
```

既存Chromeを使う場合は `PPTXGEN_CHROMIUM` にChrome実行ファイルの絶対パスを指定します。
`--ratio 4:3` で1440×1080、通常は1920×1080。`--theme client_a` でThemeを選択。
初回の生成結果は `html/`、`images/`、`preview.html`、`qa_report.json`、`review_manifest.json`。
QA通過後も人の承認までは `presentation.pptx` を生成しません。`--approve` は既存のレビュー済みHTML/PNGを再生成せず、そのままPPTXへパッケージします。
プレビューの画像をクリックすると原寸で確認できます。PPTX内の内容は画像であり直接編集できません。

## 作業の進め方

このリポジトリは「入力データを作る場所」と「描画・検証する仕組み」を分けて運用します。案件固有の入力JSON、ロゴ、生成物は作業用ディレクトリで管理し、リポジトリには汎用的な基盤の変更だけを残します。

### 1. 作業環境を準備する

初回だけ依存関係とChromiumを準備します。

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
```

案件ごとに、リポジトリ外へ入力JSONと出力先を用意します。たとえば `work/brief.json` を入力にする場合は、次のように実行します。

```sh
PYTHONPATH=src .venv/bin/python -m pptxgen \
  --input work/brief.json \
  --output work/output \
  --ratio 16:9
```

### 2. 入力JSONでページを設計する

まず文章と情報の構造をJSONにします。各ページには連番の `slide_number`、使用する `layout`、`title`、必要に応じて `lead` を指定します。レイアウト固有の項目は次のとおりです。

| layout | 用途 | 主な入力 |
| --- | --- | --- |
| `title` | 表紙・章扉 | `subtitle` |
| `comparison_2col` | 2つの案・観点の比較 | `left` / `right` の `heading` と `items` |
| `cards_3col` | 3つの要素・論点の整理 | `cards` 3個の `heading` と `items` |
| `role_split` | 役割・責任分界の整理 | `sections`、`key_message`、`key_note` |

この段階では、まず1ページあたりの情報量を決めます。文字が収まらない場合にフォントを無理に小さくするのではなく、文章を短くする、項目を分ける、別ページに分割する、より適したレイアウトへ変更する、という順で調整します。

### 3. HTML・PNGを生成する

初回生成ではPPTXを作らず、レビュー用のHTMLとPNGだけを作ります。

```sh
PYTHONPATH=src .venv/bin/python -m pptxgen \
  --input work/brief.json \
  --output work/output \
  --theme default \
  --ratio 16:9
```

生成される主なファイルは次のとおりです。

- `preview.html`: 全ページを一覧で確認するための入口
- `images/slide_*.png`: QAを通過した各ページの原寸画像
- `html/slide_*.html`: Chromiumが描画した各ページのHTML
- `qa_report.json`: 自動検証の結果とエラー内容
- `review_manifest.json`: 入力、テーマ、比率、ページ数の記録

`qa_report.json` が `awaiting_human_review` になっていることを確認してから、人のレビューへ進みます。エラーになった場合はPPTXを作らず、レポートの `issues` を修正して再実行します。

### 4. 人がプレビューをレビューする

ブラウザで `work/output/preview.html` を開き、一覧と各画像の原寸表示を確認します。最低限、次の観点をページごとに確認します。

- タイトルと本文が読みやすく、長い文章が不自然に折り返されていないか
- 余白、整列、カード幅、ページ番号、フッターが全ページで揃っているか
- ロゴがある場合、位置・大きさ・縦横比が正しく、本文と重なっていないか
- 色、見出し、強調の使い方がページ間で一貫しているか
- 1ページに情報を詰め込みすぎていないか、逆に空きすぎていないか

修正内容は、文章やデータなら入力JSON、見た目の共通ルールなら `styles/` やテーマ、特定の構造なら `src/pptxgen/layouts/` に反映します。共通Shellの変更が必要な場合だけ `src/pptxgen/shell.html` を変更します。

### 5. 修正と再生成を繰り返す

レビューで問題が見つかったら、次のように原因に対応する場所を選びます。

| 問題 | 主に修正する場所 |
| --- | --- |
| 文章が長い・情報量が多い | 入力JSON |
| ページ構造が合わない | 入力JSONの `layout`、または `src/pptxgen/layouts/` |
| 色・余白・フォントを全体で変えたい | `styles/tokens.css`、`styles/common.css` |
| ロゴやヘッダーの位置を変えたい | `themes/<theme>/theme.json`、`src/pptxgen/shell.html` |
| はみ出しや重なりを検出したい | `src/pptxgen/qa.js` とテスト |

変更後は必ず同じ生成コマンドを再実行し、古いPNGを見て判断しないようにします。入力JSONと `--ratio`、`--theme`、出力先はレビュー中に固定します。

### 6. 承認後にPPTXをパッケージする

人のレビューが完了し、`qa_report.json` にエラーがないことを確認したら、同じ出力ディレクトリに対して承認処理を実行します。

```sh
PYTHONPATH=src .venv/bin/python -m pptxgen \
  --output work/output \
  --approve
```

`--approve` はHTMLやPNGを再生成せず、レビュー済みのPNGを全面画像として `presentation.pptx` にパッケージします。したがって、承認後に入力JSONやCSSを変更した場合は、承認済みの出力を使わず、最初の生成からやり直します。

### 7. 最終確認と変更の記録

PPTXを開いてページ数、比率、画像の欠落、表示順を確認します。基盤側を変更した場合はテストを実行します。

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

レビュー済みの案件入力や生成物をリポジトリへ追加する必要はありません。コミットするのは、レイアウト、テーマ、QA、ドキュメント、テストなど再利用できる変更に限定します。

## 共通ロゴ

`src/pptxgen/shell.html` だけがロゴを描画します。各Layoutは本文のみを持ちます。
優先順位は `themes/<theme>/logo.png` → `assets/logo.png`。ロゴを使う場合は、いずれかの場所にPNGを配置してください。
Themeロゴが欠損ならFallback、両方とも欠損または破損・読み込み失敗ならエラー。画像をHTMLに埋め込むため出力の移動でもリンク切れしません。

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
