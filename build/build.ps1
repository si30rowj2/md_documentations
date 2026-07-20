# ============================================================
# ソフトウェア仕様書 PDF ビルドスクリプト (Windows)
# 必要: Pandoc, TeX ディストリビューション(MiKTeX / TeX Live) ※xelatex を使用
# 実行: .\build\build.ps1  (リポジトリのルートで実行)
# ============================================================
param(
    # 本文フォント。Windows 標準なら "Yu Mincho" / "Yu Gothic"、
    # Noto を入れているなら "Noto Serif CJK JP" など
    [string]$MainFont = "Yu Mincho",
    # コードブロック用等幅フォント (日本語グリフを含むもの)
    [string]$MonoFont = "MS Gothic",
    [string]$Output   = "output\仕様書.pdf"
)

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
New-Item -ItemType Directory -Force -Path (Split-Path $Output) | Out-Null

# wiki.js 用 front matter (--- ~ ---) を除去した一時ファイルを作る
# (front matter の title が PDF のタイトルを上書きしてしまうのを防ぐ)
$tmpDir = Join-Path $env:TEMP "spec_pdf_build"
if (Test-Path $tmpDir) { Remove-Item $tmpDir -Recurse -Force }
New-Item -ItemType Directory -Path $tmpDir | Out-Null

foreach ($f in (Get-ChildItem "docs\*.md" | Sort-Object Name)) {
    $lines = Get-Content $f.FullName -Encoding UTF8
    if ($lines.Count -gt 0 -and $lines[0] -match '^---\s*$') {
        $end = 1
        while ($end -lt $lines.Count -and $lines[$end] -notmatch '^(---|\.\.\.)\s*$') { $end++ }
        $lines = $lines[($end + 1)..($lines.Count - 1)]
    }
    $lines | Set-Content (Join-Path $tmpDir $f.Name) -Encoding UTF8
}

# 数字プレフィックス順に md を結合 → 章番号は自動採番される
$files = Get-ChildItem "$tmpDir\*.md" | Sort-Object Name | ForEach-Object { $_.FullName }

pandoc @files `
    --from markdown `
    --metadata-file="build\metadata.yaml" `
    --toc --toc-depth=3 `
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

if ($LASTEXITCODE -eq 0) { Write-Host "OK: $Output" } else { Write-Error "PDF 生成に失敗しました" }
