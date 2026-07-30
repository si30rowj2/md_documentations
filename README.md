# ソフトウェア仕様書 (md → wiki.js / MkDocs / PDF・章番号は自動採番)

複数の md ファイルから、wiki.js のページ群・MkDocs の静的サイト・PDF / HTML を生成する構成のサンプル。

**章番号はどこにも書かない。** ファイル名・フォルダ名・見出しのいずれにも番号を入れず、
リポジトリ直下の **`docs.yml` 1 ファイル**が章の順序・構造・番号のすべてを決める。

```
docs.yml  ← 唯一の定義ファイル (順序・構造・メタデータ・採番設定)
   │
   ├─→ wiki.js .... tools/wikijs.py theme (表示時に採番) + push/nav (ページ・サイドバー)
   ├─→ MkDocs ..... tools/mkdocs_hook.py が nav と見出し番号を注入
   ├─→ 結合md ..... tools/render.py combine → dist/仕様書.md
   └─→ PDF/HTML ... build/build.py (結合md → pandoc)
```

採番ロジックの実装は `tools/doctree.py` の 1 箇所だけ。すべての出力がそこを通るので、
**どの出力でも章番号は完全に一致する**。

## なぜファイル名に番号を付けないのか

ファイル名の数字プレフィックス(`03_screens/01_login.md`)で順序を管理すると、
章を途中に挟むたびに後続を全部リネームすることになる。自動リネームのスクリプトを用意しても、

- ページの **URL が変わる**(wiki.js / MkDocs の外部リンク・ブックマークが切れる)
- 章を 1 つ足すだけで大量のリネームが git 履歴に残る

という問題が残る。`docs.yml` に順序を持たせれば、**章の挿入は yaml に 1 行足すだけ**で、
ファイルは 1 つも動かず URL も変わらない。

## `docs.yml`

```yaml
# 文書メタデータ (PDF の表紙・MkDocs の site_name の唯一のソース)
title: 在庫管理システム ソフトウェア仕様書
subtitle: Version 1.0
author: 株式会社サンプル 開発部
date: 2026-07-18

numbering:
  separator: "-"      # 3-1-1.  ("." にすれば 3.1.1.)
  suffix: "."
  heading_depth: 3    # md 内で採番する見出しの深さ (3 = H1..H3)

home: index.md        # 採番対象外のトップページ
output: 仕様書         # 生成ファイルのベース名 (dist/仕様書.md, output/仕様書.pdf …)

wikijs:                    # wiki.js 連携だけが読む (PDF / MkDocs には影響しない)
  path_prefix: docs        # wiki.js 上のページパス → /docs/screens/login
  locale: ja
  navigation_mode: STATIC  # サイドバーを nav の順序で組み立てる

# 並び順 = 表示順 = 章番号。記法は MkDocs の nav と同じで、任意の深さに入れ子にできる
nav:
  - 概要:
      - overview/overview.md
  - システム構成:
      - architecture/architecture.md
  - 画面仕様:
      - screens/login.md
      - screens/stock_search.md
      - screens/receiving.md
      - screens/shipping.md
  - API仕様:
      - api/stocks.md
      - api/receiving.md
```

**ページのタイトルは `docs.yml` に書かない。** 各 md の front matter の `title:`
(無ければ H1)から自動で取る。二重定義を避けるため、`docs.yml` に書くのはセクション名だけ。

## 採番モデル

| レベル | 由来 | 例 |
|--------|------|-----|
| セクション | `docs.yml` の nav 項目 | `3.` 画面仕様 |
| ページ | nav 内のファイル (= md の H1) | `3-1.` ログイン画面 |
| 中項目 | ページ内の H2 | `3-1-1.` 画面仕様 |
| 小項目 | ページ内の H3 | `3-1-1-1.` 入力項目 |

- **wiki.js / MkDocs**(ページ単位表示): 1 ページ = 1 画面。H1 = `3-1.`、H2 = `3-1-1.`
- **結合md / PDF / HTML**: セクションを `#`、ページを `##` …と 1 段下げて結合し、同じ番号が付く

番号を**いつ付けるか**は出力ごとに違うが、番号を決めているのは常に `tools/doctree.py` の 1 箇所。

| 出力 | 採番のタイミング | 番号が出る場所 |
|------|-----------------|---------------|
| MkDocs | ビルド時(見出しテキストに焼き込み) | 本文・左ナビ・ページ内目次・検索結果 |
| PDF / HTML / 結合md | 結合時(見出しテキストに焼き込み) | 本文・目次 |
| wiki.js | **表示時**(ブラウザ側で付与) | 本文・ページタイトル・ページ内目次・サイドバーの表示名 |

## フォルダ構成

```
docs.yml                       ★ 唯一の定義ファイル
docs/
  index.md                     トップ (採番対象外)
  overview/overview.md         1-1 概要
  architecture/architecture.md 2-1 システム構成
  screens/                     セクション: 画面仕様
    login.md                   3-1 ログイン画面
    stock_search.md            3-2 在庫照会画面
    receiving.md               3-3 入庫登録画面
    shipping.md                3-4 出庫登録画面
  api/                         セクション: API仕様
    stocks.md                  4-1 在庫照会API
    receiving.md               4-2 入庫登録API
```

| パス | 内容 |
|------|------|
| `docs.yml` | 順序・構造・メタデータ・採番設定の唯一の定義 |
| `docs/**/*.md` | 本文。ファイル名にも見出しにも番号は書かない |
| `tools/doctree.py` | `docs.yml` のパースと採番。**採番ロジックはここだけ** |
| `tools/render.py` | CLI: `check` / `combine` |
| `tools/mkdocs_hook.py` | MkDocs に nav と見出し番号を注入するフック |
| `tools/wikijs.py` | CLI: `theme`(採番スクリプト生成)/ `push`(ページ反映)/ `nav`(サイドバー) |
| `wikijs/head-injection.html` | 生成物。wiki.js の「HTMLヘッド注入」に貼る採番スクリプト |
| `mkdocs.yml` / `requirements.txt` | MkDocs (Material) の見た目の設定・依存 |
| `build/build.py` | PDF / HTML ビルド (pandoc)。`build.ps1` / `build.sh` はその薄いラッパー |
| `build/header.tex` | PDF の LaTeX プリアンブル(改ページ・目次まわり) |
| `dist/` | 結合md の出力(`.gitignore` 済み) |
| `output/` | 生成された PDF / HTML |

## md の書き方ルール

- 1 ファイル = 1 ページ。先頭の `# 見出し` がページタイトル(1 つだけ)
- ファイル内は `##` が中項目、`###` が小項目。**見出しに番号は書かない**
- ファイル名・フォルダ名にも**番号を付けない**(`screens/login.md` のようにスラッグだけ)
- 新しい md を追加したら `docs.yml` の `nav` にも追加する(忘れると `check` が知らせる)
- 他章を参照するときは「画面仕様の章を参照」のように**章名で参照**する
  (番号は自動採番なので変わりうる)

## 事前準備

| 用途 | 必要ツール |
|------|-----------|
| `check` / 結合md / wiki.js 連携 | Python 3 + `pip install -r requirements.txt` |
| MkDocs 静的サイト | 同上 |
| PDF / HTML | 上記 + Pandoc(PDF はさらに TeX 環境の `xelatex` と日本語フォント) |

```powershell
pip install -r requirements.txt
```

### PDF 用ツールの導入 (Windows / winget)

```powershell
winget install --id JohnMacFarlane.Pandoc -e     # Pandoc
winget install --id MiKTeX.MiKTeX -e             # TeX 環境 (xelatex)
```

- インストール後は **PATH 反映のためシェル(端末)を開き直す**こと。
  PATH が通らない場合は環境変数 `PANDOC` に `pandoc.exe` のフルパスを設定してもよい。
- 日本語フォントは既定で **Yu Mincho / MS Gothic**(Windows 標準)を使用。
  Linux / macOS では **Noto Serif CJK JP / Noto Sans Mono CJK JP**。
  変更は `--main-font` / `--mono-font` 引数で行う。
- TeX 環境は macOS/Linux なら **TeX Live**(`sudo apt install texlive-xetex` 等)でも可。

#### MiKTeX 初回セットアップの注意 (重要)

MiKTeX は**インストール直後に一度「更新チェック」を済ませないと**、変換時に
`major issue: So far, you have not checked for MiKTeX updates` を出す。初回のみ次のいずれかを実施する。

```powershell
miktex packages update-package-database
miktex packages update
initexmf --set-config-value "[MPM]AutoInstall=1"
```

- または **MiKTeX Console** →「Check for updates」を 1 回実行し、
  「Always install missing packages on-the-fly」を有効化する。
- 初回ビルド時は不足 TeX パッケージ(etoolbox / titlesec 等)が自動 DL されるため時間がかかる。

## 整合性チェック

`docs.yml` と `docs/` の食い違い(未登録の md・存在しないパス・重複)を検出する。
章構成の一覧も表示されるので、番号の確認にも使える。

```powershell
python tools\render.py check
```

```
OK: 8 ページ、すべて docs.yml と一致しています
  1. 概要
    1-1. 概要  (overview/overview.md)
  ...
```

問題があると終了コード 1 を返すので、CI に組み込める。

## 結合md の作り方 (納品/受け渡し用)

```powershell
python tools\render.py combine                      # dist\仕様書.md に全結合
python tools\render.py combine --mode per-section   # dist\3_画面仕様.md … セクションごと
python tools\render.py combine --out path\to.md     # 出力先を明示
```

結合時に front matter の除去・見出しの段下げ・セクション見出しの注入・章番号の付与を行う。

## PDF / HTML の作り方

```powershell
.\build\build.ps1                                          # output\仕様書.pdf
.\build\build.ps1 --format html                            # output\仕様書.html
.\build\build.ps1 --main-font "Yu Gothic" --mono-font "BIZ UDGothic"
```

```bash
bash build/build.sh
bash build/build.sh --format html
```

`build.ps1` / `build.sh` は `build/build.py` を呼ぶだけのラッパー。`python build/build.py` を直接叩いてもよい。
内部で結合md を生成してから pandoc に渡す。表紙 → 目次(ページ番号付き) → 各セクション
(セクションごとに改ページ)の PDF が `output/仕様書.pdf` に生成される。

章番号は結合の時点で見出しに焼き込まれているため、pandoc の `--number-sections` は**使わない**。
これにより PDF の番号が MkDocs / wiki.js と完全に一致する。

## MkDocs での作り方

```bash
mkdocs serve    # http://127.0.0.1:8000 でライブプレビュー
mkdocs build    # site/ に静的サイトを生成 (site/ は .gitignore 済み)
```

- `mkdocs.yml` には**見た目の設定しか書かない**。`site_name` と `nav` は
  `tools/mkdocs_hook.py` が `docs.yml` から注入する
- 番号は見出しテキストに入るので、左ナビ・ページ内目次・検索結果にも出る
- `docs.yml` を編集すると `mkdocs serve` が自動でリロードする(`watch` 設定済み)

## wiki.js への上げ方

**wiki.js には `docs/` の md をそのまま載せる。番号は wiki.js 側の表示時に付く。**
番号を焼き込んだ md の複製(以前の `wikijs_export/`)は作らない。

### 1. 採番スクリプトを wiki.js に登録する (最初の 1 回 + `docs.yml` 変更時)

```powershell
python tools\wikijs.py theme       # wikijs\head-injection.html を生成
```

生成された HTML の中身を、wiki.js 管理画面 → **テーマ** → **「HTMLヘッド注入」**に貼り付ける。
このスクリプトが `docs.yml` の番号表を持っていて、ページを開いたときに

- 本文の見出し(H1〜`heading_depth`)
- ページタイトル・ブラウザのタブ名
- 右側のページ内目次
- 左のサイドバーの表示名

へ番号を付ける。番号の計算は `tools/doctree.py` が出した値をそのまま使うので、
**PDF / MkDocs と必ず一致する**。

> `docs.yml` の `nav` を変更したら `theme` を実行し直して貼り直すこと(番号表を埋め込んでいるため)。
> md 本文の編集だけなら貼り直しは不要。

### 2. md とサイドバーを wiki.js に反映する

```powershell
$env:WIKIJS_URL   = "http://localhost:3000"
$env:WIKIJS_TOKEN = "<管理画面 → API で発行したトークン>"

python tools\wikijs.py push --dry-run   # 何が作成/更新されるかだけ表示
python tools\wikijs.py push             # ページ + サイドバーを反映
python tools\wikijs.py push --prune     # docs.yml から外れたページを wiki.js からも削除
python tools\wikijs.py push --no-nav    # サイドバーは触らずページだけ反映
python tools\wikijs.py nav              # サイドバーだけを docs.yml の順序に更新
```

- `docs/screens/login.md` → `/docs/screens/login`。**パスに番号を含まないので、章を挿入しても URL は変わらない**
- front matter は wiki.js のメタデータ(タイトル)になるため、本文からは除いて送る
- タイトルは `3-1. ログイン画面` ではなく `ログイン画面` のまま送る(番号は表示時に付くため)
- `--prune` の対象は `path_prefix` 配下だけ。同じ wiki.js に載っている他のページは消さない

Git 連携(管理画面 → ストレージ → Git)を使う場合も、リポジトリの `docs/` がそのまま
`/docs/...` のページになるため、`push` と同じパスに揃う(サイドバーは `nav` で別途反映する)。

動作確認用の wiki.js は `docker compose up -d` で起動できる(`docker-compose.yml`)。

### サイドバーを docs.yml の順序・日本語セクション名にする

wiki.js **組み込みのサイトツリーでは、docs.yml の順序も日本語のセクション名も表現できない**。
wiki.js 2.x の実装がそうなっているため:

| | 実装 | 結果 |
|---|---|---|
| 並び順 | `server/jobs/rebuild-tree.js` の `orderBy(['localeCode', 'path'])` | **パスのアルファベット順に固定**。`api` → `architecture` → `overview` → `screens` |
| フォルダ名 | 同ファイルの `title: isFolder ? part : page.title` | **パスの断片そのまま**。`screens` は `screens` のまま(同じパスにページを置いても変わらない) |

そこで `push` / `nav` は、docs.yml から**カスタムナビゲーション**を組み立てて
GraphQL API (`navigation.updateTree`) で流し込む。これが順序と表示名を制御できる唯一の方法。

```
トップ                     ← home (index.md)
────────
[見出し] 3. 画面仕様        ← docs.yml のセクション名がそのまま日本語の見出しに
  3-1. ログイン画面         ← docs.yml の nav の順序どおり
  3-2. 在庫照会画面
  3-3. 入庫登録画面
  3-4. 出庫登録画面
────────
[見出し] 4. API仕様
  4-1. 在庫照会API
  4-2. 入庫登録API
```

- カスタムナビゲーションは**入れ子を持てない平坦なリスト**なので、セクションは
  見出し(header)と区切り線(divider)で表現する。階層は番号で読み取れる
- ラベルには番号を焼き込む(生成物なので md には影響しない)。採番スクリプト側は
  すでに番号が入っている項目には**二重に付けない**
- 表示モードは `docs.yml` の `wikijs.navigation_mode` で決まる

| 値 | サイドバー |
|---|---|
| `STATIC`(既定) | カスタムナビゲーションのみ |
| `MIXED` | カスタムナビゲーション + 組み込みサイトツリーの切替ボタン |
| `TREE` | 組み込みサイトツリーのみ(**順序・日本語名は効かなくなる**) |
| `NONE` | サイドバーなし |

> `nav` はそのロケールのカスタムナビゲーションを**丸ごと置き換える**(他ロケールのものは残す)。
> 管理画面で手作りしたリンクを併用している場合は `--no-nav` を使う。

### ページパスの先頭階層 (`/docs/...`)

リバースプロキシで `/docs` 配下を wiki.js に転送する運用に合わせ、wiki.js 上のページは
`docs/` 始まりにしている。設定は `docs.yml` の 1 箇所:

```yaml
wikijs:
  path_prefix: docs      # screens/login.md → /docs/screens/login
  locale: ja
  navigation_mode: STATIC
```

`push`(ページの作成先)・`nav`(サイドバーのリンク先)・`theme`(採番スクリプトが
ページを引き当てる先)の**すべてがこの値を見る**ので、変更しても食い違わない。
ただし `theme` の再実行と貼り直しが必要。

採番スクリプトは `/docs/screens/login` のほか、`/ja/docs/screens/login`(多言語構成)と
`/screens/login`(プロキシがプレフィックスを落として wiki.js に渡す構成)でも引き当てられる。
`path_prefix` を空にすればプレフィックス無し(`/screens/login`)になる。
コマンドラインから一時的に変えるなら `--prefix` を使う。

### この方式の制約

サイドバーの順序と表示名はカスタムナビゲーションで解決済み。残るのは、
表示時採番のため **番号が md 本文に「文字として」入っていない**ことによる制約:

- **検索結果**のタイトル・本文抜粋には番号が出ない(検索インデックスは md 本文から作られるため)
- wiki.js の**ページエクスポート / 印刷**にも番号は含まれない(番号付きの配布物は PDF を使う)
- `navigation_mode: TREE` にした場合は、組み込みサイトツリーの並び順・フォルダ名は
  wiki.js 側の仕様どおり(パス順・英語のパス断片)になる

検索結果まで番号を揃えたい場合は、番号を md に焼き込んで送る方式に切り替える必要がある。

## 章を途中に挿入するとき

**ファイルのリネームは一切不要。**

1. 番号を含まない名前で md を作る(例 `docs/screens/inventory_count.md`)
2. `docs.yml` の `nav` の入れたい位置に 1 行足す

```yaml
  - 画面仕様:
      - screens/login.md
      - screens/stock_search.md
      - screens/inventory_count.md    # ← ここに挿入
      - screens/receiving.md
      - screens/shipping.md
```

これだけで後続の番号(`3-4.` `3-5.` …)がすべての出力で自動的に繰り下がる。
**既存ページの URL は変わらない。** 章の並べ替えも `docs.yml` の行を入れ替えるだけ。

## 注意事項

- 番号の書式を変えたいときは `docs.yml` の `numbering.separator` / `suffix` を変える
  (`separator: "."` なら `3.1.1.`)。全出力に同時に効く
- `numbering.heading_depth` より深い見出し(既定では H4 以降)には番号が付かない
- PDF の改ページ・目次まわりの調整は `build/header.tex`
- **PowerShell スクリプト(`.ps1`)は UTF-8 (BOM 付き) で保存すること**。Windows PowerShell 5.1 は
  BOM 無し UTF-8 を Shift-JIS として誤読し、日本語コメントが後続行を巻き込んで動作不良になるため
