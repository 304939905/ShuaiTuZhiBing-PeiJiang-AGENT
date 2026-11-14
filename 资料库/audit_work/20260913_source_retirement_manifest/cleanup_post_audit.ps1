param(
    [switch]$Execute
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$libraryRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot '..\..'))
$workspaceRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot '..\..\..'))
$workspacePrefix = $workspaceRoot.TrimEnd('\') + '\'
$mode = if ($Execute) { 'execute' } else { 'dry-run' }
$resultPath = Join-Path $scriptRoot ("POST_AUDIT_CLEANUP_" + $mode.ToUpperInvariant() + ".json")

function Assert-WorkspaceFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    $full = [System.IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith($workspacePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Target escapes workspace: $full"
    }
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) {
        throw "Target is not an existing file: $full"
    }
    return $full
}

$high = New-Object 'System.Collections.Generic.List[string]'
foreach ($name in @(
    '--png_dir',
    'scan_herojineng_full.json',
    '_active_scan_miswrite.json',
    '_active_scan_unknown.json',
    '5X5_RANDOM_AUDIT_LOCAL_EVIDENCE_20260825.json'
)) {
    $high.Add((Assert-WorkspaceFile -Path (Join-Path $libraryRoot $name)))
}
$high.Add((Assert-WorkspaceFile -Path (Join-Path $workspaceRoot '--output_dir')))

$htmlHash = '14cfbd42ef032126fbe2ed1bf7f5a3e3a42bd070dd7ab0ecdc7918462030954b'
$htmlMatches = @(
    Get-ChildItem -LiteralPath $libraryRoot -File -Filter '*.html' |
        Where-Object { (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -eq $htmlHash }
)
if ($htmlMatches.Count -ne 1) {
    throw "Expected exactly one historical embedded-image HTML by SHA-256, found $($htmlMatches.Count)."
}
$high.Add((Assert-WorkspaceFile -Path $htmlMatches[0].FullName))

$exactOptionalNames = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($name in @(
    '_test.docx', '_test.json', 'FINAL_AUDIT_RAW.txt', '_verify_residuals.txt',
    '_phaseA_docx_scan.txt', '_phaseA_docx_scan2.txt', '_phaseA_gate_report.txt',
    '_frame_check_out.txt', '_check_zr2_result.txt', '_v.txt', 'inventory_report.txt',
    'clean_impurity_log.txt', 'organize_log.txt', 'scan_baowu_digest.txt'
)) {
    [void]$exactOptionalNames.Add($name)
}

$optional = New-Object 'System.Collections.Generic.List[string]'
foreach ($item in Get-ChildItem -LiteralPath $libraryRoot -File) {
    $name = $item.Name
    $isCandidate = (
        $item.Extension.Equals('.log', [System.StringComparison]::OrdinalIgnoreCase) -or
        $name.IndexOf('.bak', [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -or
        $exactOptionalNames.Contains($name) -or
        $name.StartsWith('_gongqi_batch_', [System.StringComparison]::OrdinalIgnoreCase)
    )
    if ($isCandidate) {
        $optional.Add((Assert-WorkspaceFile -Path $item.FullName))
    }
}

$targets = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($path in $high) { [void]$targets.Add($path) }
foreach ($path in $optional) { [void]$targets.Add($path) }

if ($high.Count -ne 7) { throw "High-confidence target count changed: $($high.Count)" }
if ($optional.Count -ne 63) { throw "Optional output target count changed: $($optional.Count)" }
if ($targets.Count -ne 70) { throw "Unique target count changed: $($targets.Count)" }

$expectedBytes = [int64]16860931
$actualBytes = [int64]0
foreach ($path in $targets) { $actualBytes += (Get-Item -LiteralPath $path).Length }
if ($actualBytes -ne $expectedBytes) {
    throw "Target bytes changed: expected=$expectedBytes actual=$actualBytes"
}

$indexPath = Join-Path $libraryRoot 'reports_index_rows.json'
$rows = Get-Content -LiteralPath $indexPath -Raw -Encoding UTF8 | ConvertFrom-Json
$protected = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($row in $rows) {
    [void]$protected.Add([System.IO.Path]::GetFullPath(([string]$row.out -replace '/', '\')))
}
foreach ($name in @(
    'aa_rate_supplement.json', 'hero.json', 'hero_extra.json', 'skill.json',
    'skill_extra.json', 'official_skill_db.json', 'reports_index_rows.json',
    'reports_index.md', 'ocr_misread_map.json'
)) {
    [void]$protected.Add([System.IO.Path]::GetFullPath((Join-Path $libraryRoot $name)))
}
foreach ($path in $targets) {
    if ($protected.Contains($path)) { throw "Protected file selected: $path" }
}

$manifestItems = @(
    foreach ($path in ($targets | Sort-Object)) {
        $item = Get-Item -LiteralPath $path
        [ordered]@{
            path = $item.FullName
            bytes = [int64]$item.Length
            sha256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            class = if ($high.Contains($item.FullName)) { 'high_confidence_historical_artifact' } else { 'old_log_test_or_backup_output' }
        }
    }
)

if ($Execute) {
    foreach ($path in $targets) {
        Remove-Item -LiteralPath $path -Force
    }
}

$remaining = @($targets | Where-Object { Test-Path -LiteralPath $_ })
$result = [ordered]@{
    mode = $mode
    completed_at = (Get-Date).ToString('s')
    deletion_performed = [bool]$Execute
    high_confidence_files = $high.Count
    old_output_files = $optional.Count
    total_files = $targets.Count
    bytes = $actualBytes
    mib = [math]::Round($actualBytes / 1MB, 3)
    protected_active_reports = $rows.Count
    remaining_targets = $remaining.Count
    validation_passed = $true
    items = $manifestItems
}
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding UTF8
[pscustomobject]$result | Select-Object mode, deletion_performed, high_confidence_files, old_output_files, total_files, bytes, mib, protected_active_reports, remaining_targets, validation_passed | Format-List
