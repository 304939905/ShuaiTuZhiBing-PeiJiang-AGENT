param(
    [switch]$Execute
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$workspaceRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot '..\..\..'))
$workspacePrefix = $workspaceRoot.TrimEnd('\') + '\'
$planPath = Join-Path $scriptRoot 'FINAL_CLEANUP_DRY_RUN.json'
$sourceManifestPath = Join-Path $scriptRoot 'SOURCE_RETIREMENT_MANIFEST.json'
$resultStem = if ($Execute) { 'DELETE_EXECUTION_RESULT' } else { 'DELETE_DRY_RUN_RESULT' }
$resultJsonPath = Join-Path $scriptRoot ($resultStem + '.json')
$resultMdPath = Join-Path $scriptRoot ($resultStem + '.md')

if (-not (Test-Path -LiteralPath $planPath -PathType Leaf)) {
    throw "Cleanup plan not found: $planPath"
}
if (-not (Test-Path -LiteralPath $sourceManifestPath -PathType Leaf)) {
    throw "Source manifest not found: $sourceManifestPath"
}

$plan = Get-Content -LiteralPath $planPath -Raw -Encoding UTF8 | ConvertFrom-Json
$sourceManifest = Get-Content -LiteralPath $sourceManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json

if (-not $plan.validation.ready_for_user_scope_confirmation) {
    throw 'Plan validation is not ready.'
}
if ($plan.validation.unresolved_inactive_reports -ne 0) {
    throw 'Unresolved inactive reports remain.'
}
if ($plan.validation.protected_overlap.Count -ne 0) {
    throw 'The plan already records protected-path overlap.'
}

function Resolve-WorkspacePath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)

    if ([System.IO.Path]::IsPathRooted($RelativePath)) {
        throw "Manifest path must be relative: $RelativePath"
    }
    $full = [System.IO.Path]::GetFullPath((Join-Path $workspaceRoot ($RelativePath -replace '/', '\')))
    if (-not $full.StartsWith($workspacePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes workspace: $RelativePath -> $full"
    }
    if ($full.Equals($workspaceRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Workspace root can never be a cleanup target.'
    }
    return $full
}

$protectedFiles = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
$protectedRoots = New-Object 'System.Collections.Generic.List[string]'

foreach ($relative in $sourceManifest.must_keep.active_report_paths) {
    [void]$protectedFiles.Add((Resolve-WorkspacePath -RelativePath $relative))
}
foreach ($relative in $plan.protected.core_files) {
    [void]$protectedFiles.Add((Resolve-WorkspacePath -RelativePath $relative))
}
foreach ($item in $plan.protected.keep_inactive_reports) {
    [void]$protectedFiles.Add((Resolve-WorkspacePath -RelativePath $item.path))
}
foreach ($item in $plan.protected.audit_final_files) {
    [void]$protectedFiles.Add((Resolve-WorkspacePath -RelativePath $item.path))
}
foreach ($relative in $plan.protected.core_roots) {
    $protectedRoots.Add((Resolve-WorkspacePath -RelativePath $relative))
}

$candidateRoots = New-Object 'System.Collections.Generic.List[object]'
$candidateFiles = New-Object 'System.Collections.Generic.List[object]'
foreach ($item in $plan.directory_roots) {
    $candidateRoots.Add([pscustomobject]@{
        Relative = [string]$item.path
        Full = Resolve-WorkspacePath -RelativePath ([string]$item.path)
        ExpectedBytes = [int64]$item.bytes
        Group = [string]$item.group
    })
}
foreach ($item in $plan.explicit_files) {
    $candidateFiles.Add([pscustomobject]@{
        Relative = [string]$item.path
        Full = Resolve-WorkspacePath -RelativePath ([string]$item.path)
        ExpectedBytes = [int64]$item.bytes
        Group = [string]$item.group
    })
}

$candidateRootSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($item in $candidateRoots) {
    if (-not $candidateRootSet.Add($item.Full)) {
        throw "Duplicate candidate root: $($item.Full)"
    }
    $prefix = $item.Full.TrimEnd('\') + '\'
    foreach ($protected in $protectedFiles) {
        if ($protected.Equals($item.Full, [System.StringComparison]::OrdinalIgnoreCase) -or
            $protected.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Protected file is inside candidate root: $protected"
        }
    }
    foreach ($protectedRoot in $protectedRoots) {
        $protectedPrefix = $protectedRoot.TrimEnd('\') + '\'
        if ($protectedRoot.Equals($item.Full, [System.StringComparison]::OrdinalIgnoreCase) -or
            $protectedRoot.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase) -or
            $item.Full.StartsWith($protectedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Protected root overlaps candidate root: $protectedRoot <-> $($item.Full)"
        }
    }
}

$candidateFileSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($item in $candidateFiles) {
    if (-not $candidateFileSet.Add($item.Full)) {
        throw "Duplicate candidate file: $($item.Full)"
    }
    if ($protectedFiles.Contains($item.Full)) {
        throw "Protected file is an explicit candidate: $($item.Full)"
    }
    foreach ($protectedRoot in $protectedRoots) {
        $prefix = $protectedRoot.TrimEnd('\') + '\'
        if ($item.Full.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Explicit candidate is inside protected root: $($item.Full)"
        }
    }
}

$missingRoots = @($candidateRoots | Where-Object { -not (Test-Path -LiteralPath $_.Full -PathType Container) })
$missingFiles = @($candidateFiles | Where-Object { -not (Test-Path -LiteralPath $_.Full -PathType Leaf) })
if ($missingRoots.Count -ne 0 -or $missingFiles.Count -ne 0) {
    throw "Candidate paths changed after plan creation. Missing roots=$($missingRoots.Count), files=$($missingFiles.Count)."
}

$planHash = (Get-FileHash -LiteralPath $planPath -Algorithm SHA256).Hash.ToLowerInvariant()
$estimatedBytes = [int64]$plan.totals.bytes
$mode = if ($Execute) { 'execute' } else { 'dry-run' }
$startedAt = (Get-Date).ToString('s')

if ($Execute) {
    foreach ($item in $candidateFiles) {
        Remove-Item -LiteralPath $item.Full -Force
    }
    foreach ($item in ($candidateRoots | Sort-Object { $_.Full.Length } -Descending)) {
        Remove-Item -LiteralPath $item.Full -Recurse -Force
    }
}

$remainingRoots = @($candidateRoots | Where-Object { Test-Path -LiteralPath $_.Full })
$remainingFiles = @($candidateFiles | Where-Object { Test-Path -LiteralPath $_.Full })
$result = [ordered]@{
    mode = $mode
    started_at = $startedAt
    completed_at = (Get-Date).ToString('s')
    workspace_root = $workspaceRoot
    plan_sha256 = $planHash
    candidate_directory_roots = $candidateRoots.Count
    candidate_explicit_files = $candidateFiles.Count
    estimated_bytes = $estimatedBytes
    estimated_gib = [math]::Round($estimatedBytes / 1GB, 3)
    protected_active_reports = $sourceManifest.must_keep.active_report_paths.Count
    protected_files = $protectedFiles.Count
    protected_roots = $protectedRoots.Count
    deletion_performed = [bool]$Execute
    remaining_candidate_roots = $remainingRoots.Count
    remaining_candidate_files = $remainingFiles.Count
    validation_passed = $true
}

$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resultJsonPath -Encoding UTF8
$lines = @(
    '# Cleanup dry-run result',
    '',
    "- Mode: $mode",
    '- Safety validation: passed',
    "- Candidate directory roots: $($candidateRoots.Count)",
    "- Candidate explicit files: $($candidateFiles.Count)",
    "- Estimated space: $([math]::Round($estimatedBytes / 1GB, 3)) GiB",
    "- Protected active reports: $($sourceManifest.must_keep.active_report_paths.Count)",
    "- Deletion performed: $([bool]$Execute)",
    "- Remaining candidate roots: $($remainingRoots.Count)",
    "- Remaining candidate files: $($remainingFiles.Count)",
    '',
    'The default mode is dry-run. Deletion requires the explicit -Execute switch.'
)
$lines | Set-Content -LiteralPath $resultMdPath -Encoding UTF8
$result | Format-List
