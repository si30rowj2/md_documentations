# ============================================================
# 章番号振り直しスクリプト (Windows)
# 使い方:
#   1. 挿入したい章を「02.5_名前.md」のように小数番号で docs/ に置く
#   2. .\tools\renumber.ps1        … 変更内容のプレビュー表示のみ
#      .\tools\renumber.ps1 -Apply … 実際にリネーム実行
# 数字順(02 < 02.5 < 03)に並べ、01, 02, 03… の連番に振り直す。
# ============================================================
param(
    [switch]$Apply
)

$root = Split-Path -Parent $PSScriptRoot
$docs = Join-Path $root "docs"

# 先頭が数字のmdを抽出し、数値としてソート (02.5 は 2.5 として 02 と 03 の間に入る)
$files = Get-ChildItem "$docs\*.md" |
    Where-Object { $_.Name -match '^(\d+(?:\.\d+)?)[-_](.+)$' } |
    ForEach-Object {
        [void]($_.Name -match '^(\d+(?:\.\d+)?)[-_](.+)$')
        [pscustomobject]@{ File = $_; Num = [double]$Matches[1]; Rest = $Matches[2] }
    } |
    Sort-Object Num, { $_.File.Name }

if (-not $files) { Write-Host "対象ファイルがありません"; exit }

# 新しい名前を計算
$n = 0
$plan = foreach ($f in $files) {
    $n++
    $newName = "{0:d2}_{1}" -f $n, $f.Rest
    [pscustomobject]@{ Old = $f.File.Name; New = $newName; Changed = ($f.File.Name -cne $newName) }
}

$plan | ForEach-Object {
    if ($_.Changed) { Write-Host ("{0}  ->  {1}" -f $_.Old, $_.New) }
    else            { Write-Host ("{0}  (変更なし)" -f $_.Old) }
}

if (-not $Apply) {
    Write-Host "`n※ プレビューのみ。実行するには -Apply を付けてください" -ForegroundColor Yellow
    exit
}

# 2段階リネーム (03→04 と 02.5→03 の衝突を避けるため一旦一時名を経由)
$changed = $plan | Where-Object Changed
foreach ($p in $changed) {
    Rename-Item (Join-Path $docs $p.Old) ($p.Old + ".renaming_tmp")
}
foreach ($p in $changed) {
    Rename-Item (Join-Path $docs ($p.Old + ".renaming_tmp")) $p.New
}
Write-Host "`n完了: $($changed.Count) 件リネームしました" -ForegroundColor Green
