# ============================================================
# md 結合スクリプト (Windows)
#
# 2階層フォルダ構成 (docs/NN_大分類/NN_画面.md) の md を、
# 納品/変換用に結合して dist/ に出力する。
#
#   .\tools\combine.ps1                      … 既定(Single)。全大分類を1ファイルに結合
#   .\tools\combine.ps1 -Mode Single         … 同上 (dist\仕様書.md)
#   .\tools\combine.ps1 -Mode PerCategory     … 大分類ごとに1ファイル (dist\<大分類名>.md)
#   .\tools\combine.ps1 -Mode Single -Out x.md … 出力先を明示 (PDFビルドから利用)
#
# 各ファイルは front matter を除去し、見出しを1段下げて (# → ##) 結合する。
# 各大分類フォルダの先頭に、.pages の title を `# 大分類名` として出力する。
# → 結合後は 大分類=H1 / 画面=H2 / 画面内H2=H3 / 画面内H3=H4 となり、
#   Pandoc --number-sections で 1 / 1-1 / 1-1-1 / 1-1-1-1 と採番される。
# ============================================================
param(
    [ValidateSet('Single', 'PerCategory')]
    [string]$Mode = 'Single',
    [string]$Out  = ''
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$docs = Join-Path $root 'docs'
$dist = Join-Path $root 'dist'

# NN_ プレフィックスの数値を取り出す (なければ $null)
function Get-NumPrefix($name) {
    if ($name -match '^(\d+(?:\.\d+)?)[-_]') { return [double]$Matches[1] }
    return $null
}

# NN_ を除いたスラッグ (フォールバックの大分類名に使う)
function Get-Slug($name) {
    if ($name -match '^\d+(?:\.\d+)?[-_](.+)$') { return $Matches[1] }
    return $name
}

# .pages の title: を読む。なければフォルダのスラッグを返す
function Get-CategoryTitle($folder) {
    $pages = Join-Path $folder.FullName '.pages'
    if (Test-Path $pages) {
        foreach ($line in (Get-Content $pages -Encoding UTF8)) {
            if ($line -match '^\s*title:\s*(.+?)\s*$') { return $Matches[1] }
        }
    }
    return (Get-Slug $folder.Name)
}

# front matter を除去し、見出しを1段下げた行配列を返す (コードフェンス内は不変)
function Convert-File($path) {
    $lines = Get-Content $path -Encoding UTF8
    # front matter (先頭 --- ~ ---) を除去
    if ($lines.Count -gt 0 -and $lines[0] -match '^---\s*$') {
        $end = 1
        while ($end -lt $lines.Count -and $lines[$end] -notmatch '^(---|\.\.\.)\s*$') { $end++ }
        if ($end -lt $lines.Count) { $lines = $lines[($end + 1)..($lines.Count - 1)] }
    }
    $inFence = $false
    $out = foreach ($line in $lines) {
        if ($line -match '^\s*(```+|~~~+)') { $inFence = -not $inFence; $line; continue }
        if (-not $inFence -and $line -match '^(#{1,6})(\s)') {
            '#' + $line   # 見出しを1段下げる
        } else {
            $line
        }
    }
    return $out
}

# 大分類フォルダを番号順に取得
$folders = Get-ChildItem $docs -Directory |
    Where-Object { $_.Name -ne 'assets' -and (Get-NumPrefix $_.Name) -ne $null } |
    Sort-Object @{ Expression = { Get-NumPrefix $_.Name } }, Name

if (-not $folders) { Write-Host '対象フォルダがありません'; exit }

# 1大分類フォルダを結合して行配列にする
function Build-Category($folder) {
    $title = Get-CategoryTitle $folder
    $body = @("# $title", '')
    $files = Get-ChildItem "$($folder.FullName)\*.md" |
        Where-Object { (Get-NumPrefix $_.Name) -ne $null } |
        Sort-Object @{ Expression = { Get-NumPrefix $_.Name } }, Name
    foreach ($f in $files) {
        $body += (Convert-File $f.FullName)
        $body += ''
    }
    return $body
}

New-Item -ItemType Directory -Force -Path $dist | Out-Null

if ($Mode -eq 'Single') {
    $all = @()
    foreach ($folder in $folders) { $all += (Build-Category $folder) }
    $target = if ($Out) { $Out } else { Join-Path $dist '仕様書.md' }
    New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
    $all | Set-Content $target -Encoding UTF8
    Write-Host "OK: $target"
} else {
    foreach ($folder in $folders) {
        $title = Get-CategoryTitle $folder
        $target = Join-Path $dist ("{0}.md" -f $title)
        (Build-Category $folder) | Set-Content $target -Encoding UTF8
        Write-Host "OK: $target"
    }
}
