# ClearAssemblyCache.ps1 - Clears the VSTO assembly download cache
# Run as Administrator with Excel CLOSED

$ErrorActionPreference = "Stop"

Write-Host "=== Clear .NET Assembly Download Cache ===" -ForegroundColor Cyan
Write-Host ""

# Check if Excel is running
$excel = Get-Process -Name "EXCEL" -ErrorAction SilentlyContinue
if ($excel) {
    Write-Host "ERROR: Excel is running. Please close Excel first!" -ForegroundColor Red
    exit 1
}

# Assembly download cache locations
$cachePaths = @(
    "$env:LOCALAPPDATA\assembly",
    "$env:LOCALAPPDATA\Apps\2.0"
)

foreach ($path in $cachePaths) {
    if (Test-Path $path) {
        Write-Host "Clearing: $path" -ForegroundColor Yellow

        $sizeBefore = (Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB

        try {
            Remove-Item "$path\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  Cleared ~$([math]::Round($sizeBefore, 2)) MB" -ForegroundColor Green
        } catch {
            Write-Host "  Partial clear (some files in use): $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Not found: $path" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=== Cache Cleared ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Reinstall BigHand fresh (to restore clean DLLs)" -ForegroundColor White
Write-Host "2. Open Excel and test" -ForegroundColor White
Write-Host ""
Write-Host "The assembly cache will be rebuilt when Excel loads the add-ins." -ForegroundColor Gray
Write-Host ""
