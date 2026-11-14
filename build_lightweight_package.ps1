param(
    [string]$PackageRoot = 'D:\Desktop\shandou\交付\率土之滨_AI配将轻量版_20260828',
    [string]$ZipPath = 'D:\Desktop\shandou\交付\率土之滨_AI配将轻量版_20260828.zip'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = 'D:\Desktop\shandou'

if (Test-Path -LiteralPath $PackageRoot) {
    throw "输出目录已存在，拒绝覆盖：$PackageRoot"
}
if (Test-Path -LiteralPath $ZipPath) {
    throw "压缩包已存在，拒绝覆盖：$ZipPath"
}

function Copy-RelativeFile {
    param([string]$Source, [string]$Base, [string]$DestinationRoot)
    $relative = $Source.Substring($Base.Length).TrimStart('\', '/')
    $destination = Join-Path $DestinationRoot $relative
    $parent = Split-Path -Parent $destination
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Copy-Item -LiteralPath $Source -Destination $destination
}

New-Item -ItemType Directory -Force -Path $PackageRoot | Out-Null
foreach ($name in @('交接', '文档', '规则与记忆', '资料库', '报告库', '审计记录', '账号资料', '工具')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $PackageRoot $name) | Out-Null
}

# 零上下文交接与用户文档
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'HANDOFF_轻量版_20260828.md') -Destination (Join-Path $PackageRoot '交接\HANDOFF_轻量版_20260828.md')
foreach ($name in @('USAGE_MANUAL_20260825.md', 'HANDOFF_20260825.md', '待办清单_2026-08-26.md', '接手提示词.md')) {
    $source = Join-Path $ProjectRoot $name
    if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination (Join-Path $PackageRoot "文档\\$name") }
}

# 规则和记忆：完整复制；它们体积小且决定判读边界。
$memoryRoot = Join-Path $ProjectRoot '.workbuddy\memory'
Get-ChildItem -LiteralPath $memoryRoot -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $PackageRoot '规则与记忆') -Recurse
}

# 结构化资料库：根目录的文本/数据/工具 + 小型 JSON 母本；排除视频转录、审计大目录、备份、图片与缓存。
$libraryRoot = Join-Path $ProjectRoot '资料库'
$allowedExtensions = @('.json', '.md', '.py', '.ps1', '.txt')
Get-ChildItem -LiteralPath $libraryRoot -File -Force | Where-Object { $allowedExtensions -contains $_.Extension.ToLowerInvariant() } | ForEach-Object {
    Copy-RelativeFile -Source $_.FullName -Base $libraryRoot -DestinationRoot (Join-Path $PackageRoot '资料库')
}
foreach ($dirName in @('frame_json', 'frame_json_kaihuang', 'hzh_frame_json', 'saiji_frame_json', 'zhenrong_frame_json', 'reports_json', 'reports')) {
    $source = Join-Path $libraryRoot $dirName
    if (Test-Path -LiteralPath $source) {
        Copy-Item -LiteralPath $source -Destination (Join-Path $PackageRoot "资料库\\$dirName") -Recurse
    }
}

# 配将核心服务：仅复制可执行源码、规则说明和示例，排除 __pycache__ 等缓存。
$serviceRoot = Join-Path $ProjectRoot '工具\配将服务'
Get-ChildItem -LiteralPath $serviceRoot -File | Where-Object {
    @('.py', '.md', '.json') -contains $_.Extension.ToLowerInvariant()
} | ForEach-Object {
    Copy-RelativeFile -Source $_.FullName -Base $ProjectRoot -DestinationRoot $PackageRoot
}

# 学习成品：只保留精编/精修报告及账号诊断示例，排除逐帧1秒版与其他中间报告。
$reportRoot = Join-Path $ProjectRoot '报告库'
Get-ChildItem -LiteralPath $reportRoot -Recurse -File -Filter '*.docx' | Where-Object {
    $_.Name -like '*精修学习报告.docx' -or $_.Name -like '*精编学习报告.docx' -or $_.FullName -like '*账号诊断*'
} | ForEach-Object {
    Copy-RelativeFile -Source $_.FullName -Base $reportRoot -DestinationRoot (Join-Path $PackageRoot '报告库')
}

# 保留可帮助接手者理解风险状态的轻量审计记录，不复制 audit_work 的图片、候选渲染或备份。
foreach ($source in @(
    (Join-Path $libraryRoot 'FULL_RISK_SCAN_20260825.md'),
    (Join-Path $libraryRoot '5X5_RANDOM_AUDIT_TODO_20260825.md'),
    (Join-Path $libraryRoot 'audit_work\20260825_canonical_migration_preview\README.md'),
    (Join-Path $libraryRoot 'audit_work\20260825_canonical_migration_preview\canonical_manifest.json'),
    (Join-Path $libraryRoot 'audit_work\20260825_canonical_migration_preview\RANDOM_REPORT_STATIC_AUDIT_20260825.md')
)) {
    if (Test-Path -LiteralPath $source) {
        Copy-Item -LiteralPath $source -Destination (Join-Path $PackageRoot (Join-Path '审计记录' (Split-Path -Leaf $source)))
    }
}

$manifest = Get-ChildItem -LiteralPath $PackageRoot -Recurse -File | Sort-Object FullName | ForEach-Object {
    $relative = $_.FullName.Substring($PackageRoot.Length).TrimStart('\', '/')
    [pscustomobject]@{
        path = $relative
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PackageRoot 'PACKAGE_MANIFEST.json') -Encoding utf8

Compress-Archive -LiteralPath (Get-ChildItem -LiteralPath $PackageRoot -Force | Select-Object -ExpandProperty FullName) -DestinationPath $ZipPath -CompressionLevel Optimal

$size = (Get-Item -LiteralPath $ZipPath).Length
Write-Output "PACKAGE_ROOT=$PackageRoot"
Write-Output "ZIP_PATH=$ZipPath"
Write-Output "FILES=$($manifest.Count)"
Write-Output "ZIP_BYTES=$size"
