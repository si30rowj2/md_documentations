# ============================================================
# ソフトウェア仕様書 PDF ビルドスクリプト (Windows)
# 必要: Pandoc, TeX ディストリビューション(MiKTeX / TeX Live) ※xelatex を使用
# 実行: .\build\build.ps1  (リポジトリのルートで実行)
#
# 2階層フォルダ構成 (docs/NN_大分類/NN_画面.md) を tools\combine.ps1 で
# 1つの md に結合してから pandoc に渡す。結合時に front matter 除去・
# 見出しの1段下げ・大分類見出し(# 大分類名)の注入が行われるため、
# pandoc --number-sections で 1 / 1-1 / 1-1-1 / 1-1-1-1 と自動採番される。
# ============================================================
param(
    # 本文フォント。Windows 標準なら "Yu Mincho" / "Yu Gothic"、
    # Noto を入れているなら "Noto Serif CJK JP" など
    [string]$MainFont = "Yu Mincho",
    # コードブロック用等幅フォント (日本語グリフを含むもの)
    [string]$MonoFont = "MS Gothic",
    [string]$Output   = "output\仕様書.pdf"
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
New-Item -ItemType Directory -Force -Path (Split-Path $Output) | Out-Null

# docs/ を1つの md に結合 (大分類フォルダを結合し見出しを整える)
$merged = Join-Path $env:TEMP "spec_pdf_build\仕様書.md"
& (Join-Path $PSScriptRoot "..\tools\combine.ps1") -Mode Single -Out $merged

# pandoc(xelatex)は MiKTeX の非致命警告 (例: "you have not checked for
# MiKTeX updates") を stderr に出す。ErrorActionPreference='Stop' のままだと
# PowerShell がそれを致命エラー扱いして PDF 生成後でも停止するため、この
# 呼び出しの間だけ 'Continue' にし、成否は $LASTEXITCODE で判定する。
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
pandoc $merged `
    --from markdown `
    --metadata-file="build\metadata.yaml" `
    --toc --toc-depth=4 `
    --number-sections `
    --pdf-engine=xelatex `
    --include-in-header="build\header.tex" `
    -V documentclass=article `
    -V mainfont="$MainFont" `
    -V monofont="$MonoFont" `
    -V papersize=a4 `
    -V geometry:margin=25mm `
    -V colorlinks=true `
    -V linkcolor=blue `
    -o $Output
$pandocExit = $LASTEXITCODE
$ErrorActionPreference = $prevEAP

if ($pandocExit -eq 0) { Write-Host "OK: $Output" } else { Write-Error "PDF 生成に失敗しました" }
