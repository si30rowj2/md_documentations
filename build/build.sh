#!/usr/bin/env bash
# ソフトウェア仕様書 PDF ビルドスクリプト (Linux/macOS)
# 必要: pandoc, xelatex (texlive), xeCJK, 日本語フォント
# 実行: bash build/build.sh  (リポジトリのルートで実行)
#
# 2階層フォルダ構成 (docs/NN_大分類/NN_画面.md) を tools/combine.sh で
# 1つの md に結合してから pandoc に渡す。結合時に front matter 除去・
# 見出しの1段下げ・大分類見出し(# 大分類名)の注入が行われるため、
# pandoc --number-sections で 1 / 1-1 / 1-1-1 / 1-1-1-1 と自動採番される。
set -euo pipefail
cd "$(dirname "$0")/.."

MAIN_FONT="${MAIN_FONT:-Noto Serif CJK JP}"
MONO_FONT="${MONO_FONT:-Noto Sans Mono CJK JP}"
OUTPUT="${OUTPUT:-output/仕様書.pdf}"
mkdir -p "$(dirname "$OUTPUT")"

# docs/ を1つの md に結合 (大分類フォルダを結合し見出しを整える)
MERGED=$(mktemp -d)/仕様書.md
bash tools/combine.sh --mode single --out "$MERGED"

pandoc "$MERGED" \
    --from markdown \
    --metadata-file=build/metadata.yaml \
    --toc --toc-depth=4 \
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
