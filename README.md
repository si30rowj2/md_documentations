# ソフトウェア仕様書 (md → wiki.js / PDF 両対応・自動採番)

複数の md ファイルから、wiki.js のページ群と 1 つの PDF の両方を生成する構成のサンプル。
**md 内の見出しには章番号を書かない**。番号はプレビュー/変換時に自動採番されるため、
章の挿入・入れ替え時に本文の修正は不要。

## 仕組みの全体像

```
docs/*.md (見出しに番号なし・ファイル名の数字プレフィックスで順序管理)
   ├─→ wiki.js ...... CSSカウンタ + パスの数字から章番号を注入するJS で自動採番
   └─→ PDF .......... Pandoc --number-sections で自動採番・目次(ページ番号付き)自動生成
```

## フォルダ構成

| パス | 内容 |
|------|------|
| `docs/` | 仕様書本体。1ファイル=1章。`01_overview.md` の数字が章番号=表示順 |
| `wikijs/custom-css.css` | wiki.js 管理画面「テーマ → CSSオーバーライド」に貼る採番CSS |
| `wikijs/head-injection.html` | 同「HTMLヘッド注入」に貼る章番号注入スクリプト |
| `build/build.ps1` / `build.sh` | PDF ビルドスクリプト (Windows / Linux) |
| `build/header.tex` | 採番形式(1, 1-1, 1-1-1)・章ごと改ページ・日本語設定 |
| `build/metadata.yaml` | PDF の表紙情報(タイトル・版・日付) |
| `output/仕様書.pdf` | 生成されたサンプル PDF |

## md の書き方ルール

- 1 ファイル = 1 章。先頭の `# 見出し` が章タイトル(1つだけ)
- `##` が中項目(1-1)、`###` が小項目(1-1-1)
- 見出しに番号は**書かない**
- ファイル名は `NN_名前.md`(NN = 章番号 2 桁)。章を途中に挿入する場合は
  後続ファイルの **ファイル名の NN だけ**リネームすればよく、本文は無修正

## wiki.js 側の設定 (1回だけ)

1. 管理画面 → **テーマ** → 「CSSオーバーライド」に `wikijs/custom-css.css` の内容を貼り付け
2. 同画面の「HTMLヘッド注入」に `wikijs/head-injection.html` の内容を貼り付け
3. ページのパス(スラッグ)は md ファイル名に合わせる (例: `/spec/01_overview`)。
   Git 連携でフォルダごと同期すればパスは自動で一致する

スクリプトがパス末尾の数字 (`01_overview` → 1) を章番号として CSS カウンタに設定し、
ページ内の H1/H2/H3 に `1.` `1-1.` `1-1-1.` が表示される。
数字プレフィックスのないページ(トップ等)には番号は付かない。

※ セレクタ `.contents` は wiki.js 2.x 標準テーマの本文コンテナ。テーマ変更時は
ブラウザの開発者ツールで本文の要素を確認し、CSS/JS 両方のセレクタを合わせること。

## wiki.js への上げ方

### 方法1: Git 連携 (推奨)

md を Git リポジトリで管理し、wiki.js に自動同期させる。

1. `docs/` を含むリポジトリを GitHub / GitLab / 社内 Git に push
2. wiki.js 管理画面 → **ストレージ** → **Git** を有効化
   - リポジトリURL・ブランチ・認証(SSH鍵 or アクセストークン)を設定
   - 同期方向: 「双方向」または「リポジトリからプル」
3. 「今すぐ同期」を実行 → `docs/01_overview.md` が `/docs/01_overview` のページになる

以後は push するだけで wiki.js に反映される(既定で5分間隔同期)。
各 md 先頭の front matter (`title:` 等) が wiki.js のページタイトルになる。
※ front matter は PDF ビルド時に自動除去されるので PDF には影響しない。

### 方法2: 手動でページ作成 (少量・お試し向け)

1. wiki.js で「新規ページ」→ エディタは **Markdown** を選択
2. ページパスを md ファイル名に合わせる (例: `docs/01_overview`)
   ※ パス末尾の数字プレフィックスが章番号になるため必須
3. front matter を除いた本文を貼り付けて保存

### 方法3: GraphQL API で一括投入 (ページ数が多い場合)

wiki.js の API (`/graphql`, `pages.create` ミューテーション) をスクリプトから叩いて一括登録できる。
管理画面 → API でキーを発行して使用する。

## PDF の作り方

必要ツール: [Pandoc](https://pandoc.org/installing.html)、TeX 環境(MiKTeX または TeX Live。`xelatex` を使用)

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

`docs/*.md` がファイル名順に結合され、表紙 → 目次(ページ番号付き) → 各章(章ごとに改ページ)
の PDF が `output/仕様書.pdf` に生成される。章番号・目次とも自動生成。
PDF のしおり(ブックマーク)も自動で付く。

## 章を途中に挿入するときの例

「2. システム構成」と「3. 機能仕様」の間に「非機能要件」を挿入する場合、
**手でリネームする必要はない**。小数番号で置いてスクリプトで振り直す。

1. `02.5_nonfunctional.md` を新規作成(02と03の間なら 02.1〜02.9 どれでも可。見出しに番号は書かない)
2. 振り直しスクリプトを実行:

   ```powershell
   .\tools\renumber.ps1          # プレビュー(何がどうリネームされるか表示のみ)
   .\tools\renumber.ps1 -Apply   # 実行
   ```

   ```bash
   bash tools/renumber.sh          # プレビュー
   bash tools/renumber.sh --apply  # 実行
   ```

   → `02.5_nonfunctional.md` が `03_nonfunctional.md` に、旧 `03_functions.md` が
   `04_functions.md` に一括リネームされる(何章あっても後続すべて自動)

3. wiki.js は Git 連携なら push で自動反映。PDF は再ビルドするだけ

※ リネームされた章は wiki.js のページパス(URL)が変わる点に注意。
ブックマークや外部からのリンクがある場合は周知するか、wiki.js 側でリダイレクトを設定する。

本文中で他章を参照する際は「機能仕様の章を参照」のように**章名で参照**し、
番号では参照しないこと(番号は自動採番のため変わりうる)。

## 注意事項

- wiki.js のサイドバー目次(ページ内ナビ)には番号は表示されない(見出しテキスト自体には番号を持たないため)
- PDF の採番形式(1-1 など)は `build/header.tex` で変更可能。`1.1` 形式にしたい場合は
  `\renewcommand{\thesubsection}` の 2 行を削除する
