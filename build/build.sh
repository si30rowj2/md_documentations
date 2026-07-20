#!/usr/bin/env bash
# ソフトウェア仕様書 PDF ビルドスクリプト (Linux/macOS)
# 必要: pandoc, xelatex (texlive), xeCJK, 日本語フォント
# 実行: bash build/build.sh  (リポジトリのルートで実行)
set -euo pipefail
cd "$(dirname "$0")/.."

MAIN_FONT="${MAIN_FONT:-Noto Serif CJK JP}"
MONO_FONT="${MONO_FONT:-Noto Sans Mono CJK JP}"
OUTPUT="${OUTPUT:-output/仕様書.pdf}"
mkdir -p "$(dirname "$OUTPUT")"

# wiki.js 用 front matter (--- ~ ---) を除去した一時ファイルを作る
# (front matter の title が PDF のタイトルを上書きしてしまうのを防ぐ)
TMPDIR_BUILD=$(mktemp -d)
trap 'rm -rf "$TMPDIR_BUILD"' EXIT
for f in docs/*.md; do
  awk 'NR==1 && /^---[[:space:]]*$/ {fm=1; next}
       fm==1 && /^(---|\.\.\.)[[:space:]]*$/ {fm=0; next}
       fm==1 {next}
       {print}' "$f" > "$TMPDIR_BUILD/$(basename "$f")"
done

# 数字プレフィックス順に md を結合 → 章番号は自動採番される
pandoc "$TMPDIR_BUILD"/*.md \
    --from markdown \
    --metadata-file=build/metadata.yaml \
    --toc --toc-depth=3 \
    --number-sections \
    --pdf-engine=xelatex \
    --include-in-header=build/header.tex \
    -V documentclass=article \
    -V mainfont="$MAIN_FONT" \
    -V monofont="$MONO_FONT" \
    -V papersize=a4 \
    -V geometry:margin=25mm \
    -V colorlinks=true \
    -V linkcolor=blue \
    -o "$OUTPUT"

echo "OK: $OUTPUT"
