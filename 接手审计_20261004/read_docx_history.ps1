$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$auditRoot = Split-Path -Parent $PSCommandPath
$workspaceRoot = Split-Path -Parent $auditRoot
$reportRoot = Join-Path $workspaceRoot '报告库'
$allReports = @(Get-ChildItem -LiteralPath $reportRoot -Recurse -Filter '*.docx')
$result = foreach ($report in $allReports) {
    $archive = [IO.Compression.ZipFile]::OpenRead($report.FullName)
    try {
        $entry = $archive.GetEntry('word/document.xml')
        if (-not $entry) { throw ('Missing document.xml: ' + $report.FullName) }
        $reader = [IO.StreamReader]::new($entry.Open())
        try { [xml]$xml = $reader.ReadToEnd() } finally { $reader.Dispose() }
        $namespace = [Xml.XmlNamespaceManager]::new($xml.NameTable)
        $namespace.AddNamespace('w','http://schemas.openxmlformats.org/wordprocessingml/2006/main')
        $paragraphs = @()
        $index = 0
        foreach ($paragraph in $xml.SelectNodes('//w:p',$namespace)) {
            $index++
            $parts = @($paragraph.SelectNodes('.//w:t',$namespace) | ForEach-Object { $_.InnerText })
            $text = $parts -join ''
            if ($text.Trim()) { $paragraphs += [PSCustomObject]@{ p = $index; text = $text } }
        }
        [PSCustomObject]@{
            path = $report.FullName.Substring($workspaceRoot.Length+1)
            paragraphs = $paragraphs
            paragraphs_including_empty = $index
            nonempty_paragraphs = $paragraphs.Count
            chars = ($paragraphs | ForEach-Object { $_.text.Length } | Measure-Object -Sum).Sum
        }
    } finally { $archive.Dispose() }
}
$result | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $auditRoot 'docx只读提取_历史审计.json') -Encoding utf8
$result | Select-Object path,nonempty_paragraphs,chars | ConvertTo-Json -Depth 3
