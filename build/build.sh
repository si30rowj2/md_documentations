#!/usr/bin/env bash
# ============================================================
# PDF / HTML ビルドの薄いラッパー (Linux/macOS)
# 実体は build/build.py。引数はそのまま渡される。
#
#   bash build/build.sh
#   bash build/build.sh --format html
#   bash build/build.sh --main-font "Noto Serif CJK JP"
#
# 必要: pandoc, xelatex (texlive-xetex), 日本語フォント
# ============================================================
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"

# リポジトリ内に仮想環境があればそちらの python を使う
python="$root/.venv/bin/python"
[ -x "$python" ] || python="$(command -v python3 || command -v python)"

exec "$python" "$root/build/build.py" "$@"
