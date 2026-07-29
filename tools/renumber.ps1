# ============================================================
# 番号振り直しスクリプト (Windows) — 2階層フォルダ構成対応
#
# 大分類 = docs 直下のフォルダ (NN_大分類)、
# 小分類 = 各フォルダ内のファイル (NN_画面.md) の両方を振り直す。
#
# 使い方:
#   1. 挿入したい大分類は「02.5_名前」フォルダ、
#      挿入したい画面は「01.5_名前.md」のように小数番号で置く
#   2. .\tools\renumber.ps1        … 変更内容のプレビュー表示のみ
#      .\tools\renumber.ps1 -Apply … 実際にリネーム実行
# 数値順(02 < 02.5 < 03)に並べ、01, 02, 03… の連番に振り直す。
# ============================================================
param(
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$docs = Join-Path $root 'docs'

# 数値プレフィックスを持つ項目を番号順に並べ、01,02… へ振り直す計画を返す。
# $items: Name プロパティを持つオブジェクト列 (FileInfo/DirectoryInfo)
function Get-RenumberPlan($items) {
    $parsed = $items |
        Where-Object { $_.Name -match '^(\d+(?:\.\d+)?)[-_](.+)$' } |
        ForEach-Object {
            [void]($_.Name -match '^(\d+(?:\.\d+)?)[-_](.+)$')
            [pscustomobject]@{ Item = $_; Num = [double]$Matches[1]; Rest = $Matches[2] }
        } |
        Sort-Object Num, { $_.Item.Name }
    $n = 0
    foreach ($p in $parsed) {
        $n++
        $newName = '{0:d2}_{1}' -f $n, $p.Rest
        [pscustomobject]@{
            Dir     = $p.Item.Directory.FullName
            Old     = $p.Item.Name
            New     = $newName
            Changed = ($p.Item.Name -cne $newName)
        }
    }
}

# 衝突回避の2段階リネームを1グループ(同一ディレクトリ内)に適用
function Invoke-Renames($plan) {
    $changed = $plan | Where-Object Changed
    foreach ($p in $changed) {
        Rename-Item (Join-Path $p.Dir $p.Old) ($p.Old + '.renaming_tmp')
    }
    foreach ($p in $changed) {
        Rename-Item (Join-Path $p.Dir ($p.Old + '.renaming_tmp')) $p.New
    }
    return $changed.Count
}

# --- 計画の作成 ---
# 大分類フォルダ (assets は対象外)
$folderPlan = Get-RenumberPlan (Get-ChildItem $docs -Directory | Where-Object { $_.Name -ne 'assets' })

# 小分類ファイル (各フォルダ内 *.md) — フォルダ名変更前の現パスで計画
$filePlans = @{}
foreach ($folder in (Get-ChildItem $docs -Directory | Where-Object { $_.Name -ne 'assets' })) {
    $filePlans[$folder.FullName] = Get-RenumberPlan (Get-ChildItem "$($folder.FullName)\*.md")
}

# --- プレビュー表示 ---
Write-Host '== 大分類フォルダ ==' -ForegroundColor Cyan
foreach ($p in $folderPlan) {
    if ($p.Changed) { Write-Host ('  {0}  ->  {1}' -f $p.Old, $p.New) }
    else            { Write-Host ('  {0}  (変更なし)' -f $p.Old) }
}
foreach ($folder in ($filePlans.Keys | Sort-Object)) {
    Write-Host ('== {0} 内の画面ファイル ==' -f (Split-Path $folder -Leaf)) -ForegroundColor Cyan
    foreach ($p in $filePlans[$folder]) {
        if ($p.Changed) { Write-Host ('  {0}  ->  {1}' -f $p.Old, $p.New) }
        else            { Write-Host ('  {0}  (変更なし)' -f $p.Old) }
    }
}

if (-not $Apply) {
    Write-Host "`n※ プレビューのみ。実行するには -Apply を付けてください" -ForegroundColor Yellow
    exit
}

# --- 実行 ---
# 先にファイル(現フォルダパス基準)を振り直し、その後フォルダを振り直す
$count = 0
foreach ($folder in $filePlans.Keys) { $count += (Invoke-Renames $filePlans[$folder]) }
$count += (Invoke-Renames $folderPlan)
Write-Host "`n完了: $count 件リネームしました" -ForegroundColor Green
