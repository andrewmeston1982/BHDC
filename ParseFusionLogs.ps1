# ParseFusionLogs.ps1 - Analyzes Fusion logs for binding failures

$logPath = "C:\FusionLogs\Default\EXCEL.EXE"

Write-Host "=== Fusion Log Analysis ===" -ForegroundColor Cyan
Write-Host ""

if (!(Test-Path $logPath)) {
    Write-Host "Log path not found: $logPath" -ForegroundColor Red
    exit 1
}

# Get all log files
$logFiles = Get-ChildItem $logPath -Filter "*.HTM" -ErrorAction SilentlyContinue

Write-Host "Found $($logFiles.Count) log files" -ForegroundColor Yellow
Write-Host ""

# Look for failures
Write-Host "=== FAILURES ===" -ForegroundColor Red
Write-Host ""

$failures = @()

foreach ($file in $logFiles) {
    $content = Get-Content $file.FullName -Raw

    # Check if this is a failure
    if ($content -match "The operation failed" -or $content -match "ERR:" -or $content -match "could not be found") {
        $failures += @{
            File = $file.Name
            Content = $content
        }

        # Extract assembly name from filename (format: AssemblyName, Version=x.x.x.x, ...)
        $asmName = $file.BaseName -replace ',.*', ''

        Write-Host "FAILED: $asmName" -ForegroundColor Red
        Write-Host "  File: $($file.Name)" -ForegroundColor Gray

        # Try to extract the actual error
        if ($content -match "LOG: .*(could not be found|failed|error).*") {
            Write-Host "  $($Matches[0])" -ForegroundColor Yellow
        }
        Write-Host ""
    }
}

if ($failures.Count -eq 0) {
    Write-Host "No obvious failures found in log files." -ForegroundColor Green
    Write-Host ""
}

# Show assemblies related to our suspects
Write-Host "=== SUSPECT ASSEMBLIES ===" -ForegroundColor Yellow
Write-Host ""

$suspects = @(
    "System.Runtime.CompilerServices.Unsafe",
    "System.Memory",
    "System.Text.Json",
    "Microsoft.Bcl.AsyncInterfaces",
    "System.Diagnostics.DiagnosticSource",
    "System.Buffers",
    "System.Numerics.Vectors"
)

foreach ($suspect in $suspects) {
    $matches = $logFiles | Where-Object { $_.Name -like "*$suspect*" }

    if ($matches) {
        Write-Host "$suspect" -ForegroundColor Cyan
        foreach ($m in $matches) {
            $content = Get-Content $m.FullName -Raw
            $status = if ($content -match "The operation failed|ERR:") { "FAILED" } else { "OK" }
            $color = if ($status -eq "FAILED") { "Red" } else { "Green" }

            # Extract version requested
            if ($content -match "LOG: Attempting download of new URL file:///.*?([^/]+\.dll)") {
                Write-Host "  Loaded from: $($Matches[1])" -ForegroundColor Gray
            }

            Write-Host "  Status: $status" -ForegroundColor $color
        }
        Write-Host ""
    }
}

Write-Host "=== FULL FAILURE DETAILS ===" -ForegroundColor Red
Write-Host "(First 3 failures)" -ForegroundColor Gray
Write-Host ""

$count = 0
foreach ($fail in $failures) {
    if ($count -ge 3) { break }

    Write-Host "--- $($fail.File) ---" -ForegroundColor Yellow
    # Show just the important parts
    $lines = $fail.Content -split "`n" | Where-Object { $_ -match "LOG:|ERR:|Assembly manager|calling assembly" }
    $lines | ForEach-Object { Write-Host $_ }
    Write-Host ""
    $count++
}

Write-Host ""
Write-Host "To view full logs, open: $logPath" -ForegroundColor Gray
Write-Host ""
