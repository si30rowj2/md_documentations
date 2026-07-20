#!/usr/bin/env bash
# 章番号振り直しスクリプト (Linux/macOS)
# 使い方:
#   1. 挿入したい章を「02.5_名前.md」のように小数番号で docs/ に置く
#   2. bash tools/renumber.sh          … プレビューのみ
#      bash tools/renumber.sh --apply … 実際にリネーム実行
set -euo pipefail
cd "$(dirname "$0")/../docs"

APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

# 数値順にソートした一覧を作る (02.5 は 02 と 03 の間)
mapfile -t sorted < <(
  for f in *.md; do
    [[ $f =~ ^([0-9]+(\.[0-9]+)?)[-_](.+)$ ]] || continue
    printf '%s\t%s\t%s\n' "${BASH_REMATCH[1]}" "$f" "${BASH_REMATCH[3]}"
  done | sort -t $'\t' -k1,1g -k2,2
)

declare -a olds news
n=0
for line in "${sorted[@]}"; do
  IFS=$'\t' read -r _num old rest <<< "$line"
  n=$((n + 1))
  new=$(printf '%02d_%s' "$n" "$rest")
  if [ "$old" = "$new" ]; then
    echo "$old  (変更なし)"
  else
    echo "$old  ->  $new"
    olds+=("$old"); news+=("$new")
  fi
done

if [ "$APPLY" -ne 1 ]; then
  echo
  echo "※ プレビューのみ。実行するには --apply を付けてください"
  exit 0
fi

# 2段階リネームで衝突回避
for old in "${olds[@]:-}"; do [ -n "$old" ] && mv "$old" "$old.renaming_tmp"; done
for i in "${!olds[@]}"; do mv "${olds[$i]}.renaming_tmp" "${news[$i]}"; done
echo
echo "完了: ${#olds[@]} 件リネームしました"
