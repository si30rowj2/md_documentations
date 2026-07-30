# ============================================================
# PDF / HTML ビルドの薄いラッパー (Windows)
# 実体は build\build.py。引数はそのまま渡される。
#
#   .\build\build.ps1
#   .\build\build.ps1 --format html
#   .\build\build.ps1 --main-font "Yu Gothic" --mono-font "BIZ UDGothic"
#
# 必要: Pandoc, TeX ディストリビューション(MiKTeX / TeX Live) ※xelatex を使用
# ============================================================
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

# リポジトリ内に仮想環境があればそちらの python を使う
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { $python = 'python' }

& $python (Join-Path $PSScriptRoot 'build.py') @args
exit $LASTEXITCODE
