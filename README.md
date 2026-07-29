# ソフトウェア仕様書 (md → wiki.js / MkDocs / PDF 対応・自動採番・2階層分割)

複数の md ファイルから、wiki.js のページ群・MkDocs の静的サイト・1 つの PDF を生成する構成のサンプル。
ドキュメントは **大分類フォルダ / 画面ごとの小ファイル** の2階層に分割する
(例: 画面仕様・API仕様を大分類、各画面を1md ファイル)。
**md 内の見出しには番号を書かない**。番号はプレビュー/変換時に自動採番されるため、
章の挿入・入れ替え時に本文の修正は不要。

## 仕組みの全体像

```
docs/NN_大分類/NN_画面.md  (見出しに番号なし・数字プレフィックスで順序管理)
   ├─→ wiki.js ...... CSSカウンタ + パス2階層の数字から番号を注入するJS で自動採番
   ├─→ MkDocs ....... 同方式(Material)。ナビは awesome-pages で大分類名を付与し自動生成
   └─→ PDF .......... tools/combine で1mdに結合 → Pandoc --number-sections で自動採番

tools/combine ...... 小ファイルを結合して納品用mdを生成 (大分類ごと / 全結合 を選択)
```

同じ `docs/` を3系統へ変換する。wiki.js と MkDocs は「番号を書かず、CSS カウンタと
パスの数字プレフィックス(大分類/小分類)から採番する」という同じ思想なので本文は分岐しない。
PDF は `tools/combine` で結合してから採番する。

## 採番モデル (最大4階層)

| レベル | 由来 | 例 |
|--------|------|-----|
| 大分類 | フォルダ `NN_` | `3` 画面仕様 |
| 小分類 | ファイル `NN_` (= ファイル内 H1) | `3-1` ログイン画面 |
| 中項目 | ファイル内 H2 | `3-1-1` 画面仕様 |
| 小項目 | ファイル内 H3 | `3-1-2` 処理フロー |

- **wiki.js / MkDocs**(ページ単位表示): 各ページは1画面。H1=`3-1`、H2=`3-1-1`、H3=`3-1-2`。
  大分類名(画面仕様 等)は左ナビのセクション見出しに出る(番号なし)。
- **結合md / PDF**: 大分類を `#`、各画面を `##`… と1段下げて結合し `1 / 1-1 / 1-1-1 / 1-1-1-1` で採番。

## フォルダ構成

```
docs/
  index.md                     トップ (番号対象外)
  01_overview/
    .pages          → title: 概要
    01_overview.md            1-1 概要
  02_architecture/
    .pages          → title: システム構成
    01_architecture.md        2-1 システム構成
  03_screens/                   大分類: 画面仕様
    .pages          → title: 画面仕様
    01_login.md               3-1 ログイン画面
    02_stock_search.md        3-2 在庫照会画面
    03_receiving.md           3-3 入庫登録画面
    04_shipping.md            3-4 出庫登録画面
  04_api/                       大分類: API仕様
    .pages          → title: API仕様
    01_stocks.md              4-1 在庫照会API
    02_receiving.md           4-2 入庫登録API
```

| パス | 内容 |
|------|------|
| `docs/NN_大分類/` | 大分類フォルダ。`NN` が大分類番号=表示順 |
| `docs/NN_大分類/.pages` | 大分類名の唯一のソース。`title:` をナビ名・結合mdの大分類見出しに使う |
| `docs/NN_大分類/NN_画面.md` | 1ファイル=1画面(小分類)。`NN` が小分類番号=表示順 |
| `docs/assets/numbering.css` / `numbering.js` | MkDocs 用の採番CSS/JS(wikijs 版の移植) |
| `tools/combine.ps1` / `combine.sh` | 小ファイルを結合して納品用mdを生成(`dist/`) |
| `tools/renumber.ps1` / `renumber.sh` | 大分類フォルダ・画面ファイルの番号振り直し |
| `mkdocs.yml` / `requirements.txt` | MkDocs(Material + awesome-pages)設定・依存 |
| `wikijs/custom-css.css` / `head-injection.html` | wiki.js 管理画面に貼る採番CSS/JS |
| `build/build.ps1` / `build.sh` / `header.tex` / `metadata.yaml` | PDF ビルド一式 |
| `dist/` | combine の結合md出力(`.gitignore` 済み) |
| `output/仕様書.pdf` | 生成された PDF |

## md の書き方ルール

- 1 ファイル = 1 画面(小分類)。先頭の `# 見出し` が画面タイトル(1つだけ)
- ファイル内は `##` が中項目、`###` が小項目。見出しに番号は**書かない**
- 大分類はフォルダ。フォルダ直下に `.pages`(`title: 大分類名`)を置く
- ファイル名は `NN_名前.md`、フォルダ名は `NN_名前`(NN=2桁)。番号は数字プレフィックスのみで管理し、
  途中挿入時は `tools/renumber` で振り直せば本文は無修正

## 事前準備 (必要ツールのインストール)

用途ごとに必要なツールは次のとおり。**結合md / renumber だけなら追加インストールは不要**
(Windows 標準の PowerShell / macOS・Linux の bash で動く)。

| 用途 | 必要ツール | 備考 |
|------|-----------|------|
| 結合md・renumber | PowerShell(Windows 標準) または bash | 追加インストール不要 |
| MkDocs 静的サイト | Python 3 + pip | `pip install -r requirements.txt` |
| PDF | Pandoc + TeX 環境(`xelatex`) + 日本語フォント | 下記参照。容量大 |

### PDF 用ツールの導入 (Windows / winget)

```powershell
winget install --id JohnMacFarlane.Pandoc -e     # Pandoc
winget install --id MiKTeX.MiKTeX -e             # TeX 環境 (xelatex)
```

- インストール後は **PATH 反映のためシェル(端末)を開き直す**こと。
- 日本語フォントは既定で **Yu Mincho / MS Gothic**(Windows 標準)を使用。別フォントは
  `-MainFont` / `-MonoFont` 引数で指定する(下記「PDF の作り方」)。
- TeX 環境は macOS/Linux なら MiKTeX または **TeX Live**(`sudo apt install texlive-xetex` 等)でも可。
  日本語フォント(Noto Serif/Sans CJK JP 等)を別途入れ、フォント名を引数で指定する。

#### MiKTeX 初回セットアップの注意 (重要)

MiKTeX は**インストール直後に一度「更新チェック」を済ませないと**、変換時に
`major issue: So far, you have not checked for MiKTeX updates` を出して失敗する。
初回のみ次のいずれかを実施する。

```powershell
# CLI で更新チェック + 不足パッケージ自動DL設定
miktex packages update-package-database
miktex packages update
initexmf --set-config-value "[MPM]AutoInstall=1"
```

- または **MiKTeX Console** を起動 →「Check for updates」を1回実行し、
  設定で「Always install missing packages on-the-fly」を有効化する。
- 初回ビルド時は不足 TeX パッケージ(etoolbox / titlesec 等)が自動DLされるため時間がかかる。

## 結合md の作り方 (納品/受け渡し用)

小ファイルを結合して1つ以上の md を `dist/` に生成する。**大分類ごとに1ファイル**と
**全部を1ファイルに結合**の両方を、モード引数で切り替えられる。

```powershell
# Windows
.\tools\combine.ps1                     # 既定(Single): dist\仕様書.md に全結合
.\tools\combine.ps1 -Mode PerCategory   # 大分類ごと: dist\画面仕様.md / dist\API仕様.md …
```

```bash
# Linux / macOS
bash tools/combine.sh                       # 既定(single): dist/仕様書.md
bash tools/combine.sh --mode percategory    # 大分類ごと
```

結合時に各ファイルの front matter 除去・見出しの1段下げ・大分類見出し(`# 大分類名`)の注入を行う。
結合mdにも番号は書き込まない(番号は PDF 変換時に付与)。

## wiki.js 側の設定 (1回だけ)

1. 管理画面 → **テーマ** → 「CSSオーバーライド」に `wikijs/custom-css.css` の内容を貼り付け
2. 同画面の「HTMLヘッド注入」に `wikijs/head-injection.html` の内容を貼り付け
3. ページのパス(スラッグ)は `大分類/画面`(例 `/spec/03_screens/01_login`)に合わせる。
   Git 連携でフォルダごと同期すればパスは自動で一致する

スクリプトがパス末尾2つの数字プレフィックス(`03_screens/01_login` → 3, 1)を大分類/小分類番号として
CSS カウンタに設定し、H1/H2/H3 に `3-1.` `3-1-1.` `3-1-2.` が表示される。
数字プレフィックスのないページ(トップ等)には番号は付かない。

※ セレクタ `.contents` は wiki.js 2.x 標準テーマの本文コンテナ。テーマ変更時は CSS/JS 両方のセレクタを合わせること。

## wiki.js への上げ方

### 方法1: Git 連携 (推奨)

1. `docs/` を含むリポジトリを Git に push
2. wiki.js 管理画面 → **ストレージ** → **Git** を有効化(URL・ブランチ・認証を設定、同期方向を選択)
3. 「今すぐ同期」→ `docs/03_screens/01_login.md` が `/docs/03_screens/01_login` のページになる

以後は push するだけで反映される。各 md 先頭の front matter (`title:` 等) がページタイトルになる。
※ front matter は結合/PDF ビルド時に自動除去されるので PDF には影響しない。

### 方法2/3

少量なら wiki.js で手動ページ作成(パスを `大分類/画面` に合わせる)、
大量なら GraphQL API (`pages.create`) で一括投入も可能。

## MkDocs での作り方

`docs/` を Material テーマの静的サイトに変換する。**md は無修正**。番号は
`docs/assets/numbering.css` / `numbering.js` がパスの数字プレフィックス2つから自動注入する。

```bash
pip install -r requirements.txt   # 初回のみ (mkdocs-material と awesome-pages を導入)

mkdocs serve    # http://127.0.0.1:8000 でライブプレビュー
mkdocs build    # site/ に静的サイトを生成 (site/ は .gitignore 済み)
```

- **ナビゲーション**は自動生成。大分類(フォルダ)順・画面(ファイル)順に並ぶため、
  `tools/renumber` で番号を振り直せばナビ順も自動で追従する。
- 大分類のナビ表示名は各フォルダの `.pages` の `title:`(awesome-pages プラグイン)から付く。
- 各 md 先頭の front matter (`title:`) が画面ページのタイトル・ナビ名になる。
- 採番形式を変えたい場合は `docs/assets/numbering.css` を編集する。
- ※ 左ナビの見出しには番号は付かない(見出しテキスト自体に番号を持たせていないため)。本文の H1/H2/H3 には付く。

## PDF の作り方

必要ツール: [Pandoc](https://pandoc.org/installing.html)、TeX 環境(MiKTeX または TeX Live。`xelatex` を使用)。
導入手順・MiKTeX 初回の注意は上記「[事前準備 (必要ツールのインストール)](#事前準備-必要ツールのインストール)」を参照。

```powershell
# Windows (リポジトリのルートで)
.\build\build.ps1
# フォント変更例
.\build\build.ps1 -MainFont "Yu Gothic" -MonoFont "BIZ UDGothic"
```

```bash
# Linux / macOS
bash build/build.sh
```

`build` は内部で `tools/combine`(Single)を呼び、`docs/` を1つの md に結合してから pandoc に渡す。
表紙 → 目次(ページ番号付き) → 各大分類(大分類ごとに改ページ)の PDF が `output/仕様書.pdf` に生成される。
番号(`1 / 1-1 / 1-1-1 / 1-1-1-1`)・目次・しおりは自動生成。

## 章を途中に挿入するときの例

**手でリネームする必要はない**。小数番号で置いてスクリプトで振り直す。

- 大分類を挿入: `02.5_名前/` フォルダ(+ `.pages`)を新規作成
- 画面を挿入: 対象フォルダ内に `01.5_名前.md` を新規作成(いずれも見出しに番号は書かない)

```powershell
.\tools\renumber.ps1          # プレビュー(何がどうリネームされるか表示のみ)
.\tools\renumber.ps1 -Apply   # 実行
```

```bash
bash tools/renumber.sh          # プレビュー
bash tools/renumber.sh --apply  # 実行
```

→ 大分類フォルダ・画面ファイルとも数値順(`02 < 02.5 < 03`)に `01,02,03…` の連番へ一括リネームされる
(何件あっても後続すべて自動)。wiki.js は Git 連携なら push で自動反映。PDF は再ビルドするだけ。

※ リネームされた項目は wiki.js のページパス(URL)が変わる点に注意。
本文中で他章を参照する際は「機能仕様の章を参照」のように**章名で参照**し、番号では参照しないこと(番号は自動採番のため変わりうる)。

## 注意事項

- wiki.js / MkDocs の左ナビ(ページ内・セクション見出し)には番号は表示されない(見出しテキスト自体に番号を持たないため)
- PDF の採番形式は `build/header.tex` で変更可能。`1.1` 形式にしたい場合は `\thesubsection` 等の `\renewcommand` を調整する
- **PowerShell スクリプト(`.ps1`)は UTF-8 (BOM 付き) で保存すること**。Windows PowerShell 5.1 は
  BOM 無し UTF-8 を Shift-JIS として誤読し、日本語コメントが後続行を巻き込んで動作不良になるため
