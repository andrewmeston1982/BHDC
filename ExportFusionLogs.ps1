# ExportFusionLogs.ps1 - Exports Fusion logs to a single text file

$logPath = "C:\FusionLogs\Default\EXCEL.EXE"
$outputFile = "C:\FusionLogs\FusionLogExport.txt"

Write-Host "Exporting Fusion logs to $outputFile..." -ForegroundColor Yellow

$output = @()
$output += "=== FUSION LOG EXPORT ==="
$output += "Generated: $(Get-Date)"
$output += "Source: $logPath"
$output += ""

$logFiles = Get-ChildItem $logPath -Filter "*.HTM" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime

$output += "Total log files: $($logFiles.Count)"
$output += ""

# First, list all failures
$output += "=== FAILURES ONLY ==="
$output += ""

foreach ($file in $logFiles) {
    $content = Get-Content $file.FullName -Raw

    if ($content -match "The operation failed|ERR:|could not be found|not found in") {
        $asmName = $file.BaseName -replace ',.*', ''
        $output += "FAILED: $asmName"
        $output += "File: $($file.Name)"

        # Extract key lines
        $lines = $content -split "<pre>|</pre>" | Where-Object { $_ -match "LOG:|ERR:|Assembly manager|calling assembly|operation failed" }
        foreach ($line in $lines) {
            $clean = $line -replace '<[^>]+>', '' -replace '&nbsp;', ' ' -replace '\s+', ' '
            if ($clean.Trim()) {
                $output += "  $($clean.Trim())"
            }
        }
        $output += ""
    }
}

$output += ""
$output += "=== ALL ASSEMBLY BINDINGS (Summary) ==="
$output += ""

foreach ($file in $logFiles) {
    $content = Get-Content $file.FullName -Raw
    $asmName = $file.BaseName
    $status = if ($content -match "The operation failed|ERR:") { "FAILED" } else { "OK" }

    $output += "$status : $asmName"
}

$output += ""
$output += "=== DETAILED LOGS (Failures + Suspects) ==="
$output += ""

$suspects = @(
    "System.Runtime.CompilerServices.Unsafe",
    "System.Memory",
    "System.Text.Json",
    "Microsoft.Bcl.AsyncInterfaces",
    "System.Diagnostics.DiagnosticSource",
    "System.Buffers",
    "System.Numerics.Vectors",
    "Microsoft.Mashup",
    "PowerQuery"
)

foreach ($file in $logFiles) {
    $content = Get-Content $file.FullName -Raw
    $asmName = $file.BaseName

    $isSuspect = $false
    foreach ($s in $suspects) {
        if ($asmName -like "*$s*") { $isSuspect = $true; break }
    }

    $isFailure = $content -match "The operation failed|ERR:"

    if ($isFailure -or $isSuspect) {
        $output += "=========================================="
        $output += "FILE: $($file.Name)"
        $output += "STATUS: $(if ($isFailure) { 'FAILED' } else { 'OK' })"
        $output += "=========================================="

        # Strip HTML and output content
        $text = $content -replace '<[^>]+>', "`n" -replace '&nbsp;', ' ' -replace '&#0;', ''
        $text = $text -replace '\n\s*\n', "`n" -replace '\n+', "`n"
        $output += $text.Trim()
        $output += ""
        $output += ""
    }
}

$output | Out-File $outputFile -Encoding UTF8

Write-Host ""
Write-Host "Done! Upload this file:" -ForegroundColor Green
Write-Host "  $outputFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "File size: $((Get-Item $outputFile).Length / 1KB) KB" -ForegroundColor Gray
