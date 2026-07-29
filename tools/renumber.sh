#!/usr/bin/env bash
# ============================================================
# 番号振り直しスクリプト (Linux/macOS) — 2階層フォルダ構成対応
#
# 大分類 = docs 直下のフォルダ (NN_大分類)、
# 小分類 = 各フォルダ内のファイル (NN_画面.md) の両方を振り直す。
#
# 使い方:
#   1. 挿入したい大分類は「02.5_名前」フォルダ、
#      挿入したい画面は「01.5_名前.md」のように小数番号で置く
#   2. bash tools/renumber.sh          … プレビューのみ
#      bash tools/renumber.sh --apply … 実際にリネーム実行
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/../docs"

APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

# 指定ディレクトリ内の項目(--dirs でフォルダ / 既定でファイル)を番号順に
# 振り直す。プレビュー出力し、APPLY=1 なら実行する。
renumber_group() {
  local dir="$1" kind="$2"   # kind: files | dirs
  local -a olds=() news=()
  local sorted
  if [ "$kind" = "dirs" ]; then
    sorted=$(
      for f in "$dir"/*/; do
        f="${f%/}"; b=$(basename "$f")
        [ "$b" = "assets" ] && continue
        [[ $b =~ ^([0-9]+(\.[0-9]+)?)[-_](.+)$ ]] || continue
        printf '%s\t%s\t%s\n' "${BASH_REMATCH[1]}" "$b" "${BASH_REMATCH[3]}"
      done | sort -t $'\t' -k1,1g -k2,2
    )
  else
    sorted=$(
      for f in "$dir"/*.md; do
        [ -e "$f" ] || continue
        b=$(basename "$f")
        [[ $b =~ ^([0-9]+(\.[0-9]+)?)[-_](.+)$ ]] || continue
        printf '%s\t%s\t%s\n' "${BASH_REMATCH[1]}" "$b" "${BASH_REMATCH[3]}"
      done | sort -t $'\t' -k1,1g -k2,2
    )
  fi

  local n=0 old rest new
  while IFS=$'\t' read -r _num old rest; do
    [ -n "${old:-}" ] || continue
    n=$((n + 1))
    new=$(printf '%02d_%s' "$n" "$rest")
    if [ "$old" = "$new" ]; then
      echo "  $old  (変更なし)"
    else
      echo "  $old  ->  $new"
      olds+=("$old"); news+=("$new")
    fi
  done <<< "$sorted"

  local cnt=${#olds[@]}
  if [ "$APPLY" -eq 1 ] && [ "$cnt" -gt 0 ]; then
    for old in "${olds[@]}"; do mv "$dir/$old" "$dir/$old.renaming_tmp"; done
    for i in "${!olds[@]}"; do mv "$dir/${olds[$i]}.renaming_tmp" "$dir/${news[$i]}"; done
  fi
  RENAMED=$((RENAMED + cnt))
}

RENAMED=0

# 先に各フォルダ内の画面ファイル、その後に大分類フォルダを振り直す
for folder in */; do
  folder="${folder%/}"
  [ "$folder" = "assets" ] && continue
  [ -d "$folder" ] || continue
  echo "== $folder 内の画面ファイル =="
  renumber_group "$folder" files
done

echo "== 大分類フォルダ =="
renumber_group "." dirs

if [ "$APPLY" -ne 1 ]; then
  echo
  echo "※ プレビューのみ。実行するには --apply を付けてください"
  exit 0
fi

echo
echo "完了: $RENAMED 件リネームしました"
