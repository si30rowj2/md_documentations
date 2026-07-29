#!/usr/bin/env bash
# ============================================================
# md 結合スクリプト (Linux/macOS)
#
# 2階層フォルダ構成 (docs/NN_大分類/NN_画面.md) の md を、
# 納品/変換用に結合して dist/ に出力する。
#
#   bash tools/combine.sh                      # 既定(single)。全大分類を1ファイルに結合
#   bash tools/combine.sh --mode single        # 同上 (dist/仕様書.md)
#   bash tools/combine.sh --mode percategory    # 大分類ごとに1ファイル (dist/<大分類名>.md)
#   bash tools/combine.sh --mode single --out x.md  # 出力先を明示 (PDFビルドから利用)
#
# 各ファイルは front matter を除去し、見出しを1段下げて (# → ##) 結合する。
# 各大分類フォルダの先頭に .pages の title を `# 大分類名` として出力する。
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="single"
OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE=$(echo "$2" | tr '[:upper:]' '[:lower:]'); shift 2 ;;
    --out)  OUT="$2"; shift 2 ;;
    *) echo "不明な引数: $1" >&2; exit 1 ;;
  esac
done

DIST="dist"
mkdir -p "$DIST"

# NN_ を除いたスラッグ
slug() { echo "$1" | sed -E 's/^[0-9]+(\.[0-9]+)?[-_]//'; }

# .pages の title:。なければフォルダのスラッグ
category_title() {
  local folder="$1"
  if [ -f "$folder/.pages" ]; then
    local t
    t=$(sed -nE 's/^[[:space:]]*title:[[:space:]]*(.+[^[:space:]])[[:space:]]*$/\1/p' "$folder/.pages" | head -n1)
    if [ -n "$t" ]; then echo "$t"; return; fi
  fi
  slug "$(basename "$folder")"
}

# front matter 除去 + 見出しを1段下げ (コードフェンス内は不変)
convert_file() {
  awk '
    NR==1 && /^---[[:space:]]*$/ { fm=1; next }
    fm==1 && /^(---|\.\.\.)[[:space:]]*$/ { fm=0; next }
    fm==1 { next }
    /^[[:space:]]*(```+|~~~+)/ { fence = !fence; print; next }
    !fence && /^#{1,6}[[:space:]]/ { print "#" $0; next }
    { print }
  ' "$1"
}

# 番号順に大分類フォルダを列挙
mapfile -t FOLDERS < <(
  for d in docs/*/; do
    d="${d%/}"
    b=$(basename "$d")
    [ "$b" = "assets" ] && continue
    [[ $b =~ ^([0-9]+(\.[0-9]+)?)[-_] ]] || continue
    printf '%s\t%s\n' "${BASH_REMATCH[1]}" "$d"
  done | sort -t $'\t' -k1,1g -k2,2 | cut -f2
)

[ ${#FOLDERS[@]} -eq 0 ] && { echo "対象フォルダがありません"; exit 0; }

# 1大分類を結合して標準出力へ
build_category() {
  local folder="$1"
  echo "# $(category_title "$folder")"
  echo
  mapfile -t FILES < <(
    for f in "$folder"/*.md; do
      [ -e "$f" ] || continue
      b=$(basename "$f")
      [[ $b =~ ^([0-9]+(\.[0-9]+)?)[-_] ]] || continue
      printf '%s\t%s\n' "${BASH_REMATCH[1]}" "$f"
    done | sort -t $'\t' -k1,1g -k2,2 | cut -f2
  )
  for f in "${FILES[@]:-}"; do
    [ -n "$f" ] || continue
    convert_file "$f"
    echo
  done
}

if [ "$MODE" = "single" ]; then
  TARGET="${OUT:-$DIST/仕様書.md}"
  mkdir -p "$(dirname "$TARGET")"
  : > "$TARGET"
  for folder in "${FOLDERS[@]}"; do build_category "$folder" >> "$TARGET"; done
  echo "OK: $TARGET"
elif [ "$MODE" = "percategory" ]; then
  for folder in "${FOLDERS[@]}"; do
    TARGET="$DIST/$(category_title "$folder").md"
    build_category "$folder" > "$TARGET"
    echo "OK: $TARGET"
  done
else
  echo "不明な --mode: $MODE (single | percategory)" >&2
  exit 1
fi
