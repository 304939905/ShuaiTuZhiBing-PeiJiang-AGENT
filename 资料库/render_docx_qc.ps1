param(
    [Parameter(Mandatory = $true)][string]$Document,
    [Parameter(Mandatory = $true)][string]$OutputDir
)

$ErrorActionPreference = 'Stop'
$loBin = 'C:\Program Files\LibreOffice\program'
$renderer = 'D:\Desktop\shandou\资料库\render_docx.py'
$python = 'C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe'

if (!(Test-Path -LiteralPath (Join-Path $loBin 'soffice.com'))) { throw "LibreOffice missing: $loBin" }
if (!(Test-Path -LiteralPath $renderer)) { throw "Project renderer missing: $renderer" }

$docPath = (Resolve-Path -LiteralPath $Document).Path
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$outPath = (Resolve-Path -LiteralPath $OutputDir).Path
$pdfPath = Join-Path $outPath (([IO.Path]::GetFileNameWithoutExtension($docPath)) + '.pdf')
$env:LIBREOFFICE_PROGRAM = $loBin
$projectSitePackages = 'D:\WorkBuddyData\python-env\shandou\Lib\site-packages'
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$projectSitePackages;$env:PYTHONPATH" } else { $projectSitePackages }
& $python $renderer $docPath $pdfPath $outPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
