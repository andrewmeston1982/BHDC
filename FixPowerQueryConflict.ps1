# FixPowerQueryConflict.ps1 - Run as Administrator
# Fixes BigHand/Power Query conflict by aligning System.Diagnostics.DiagnosticSource versions

$ErrorActionPreference = "Stop"

$bigHandPath = "C:\Program Files\BigHand\BigHand Document Creation"
$powerQueryPath = "C:\Program Files\Microsoft Office\root\Office16\ADDINS\Microsoft Power Query for Excel Integrated\bin"

$dllName = "System.Diagnostics.DiagnosticSource.dll"
$sourceDll = Join-Path $powerQueryPath $dllName
$targetDll = Join-Path $bigHandPath $dllName
$backupDll = Join-Path $bigHandPath "$dllName.bak"

# Config files to update
$configFiles = @(
    "Iphelion.Outline.ExcelAddIn.dll.config",
    "Iphelion.Outline.AddIn.dll.config",
    "Iphelion.Outline.WordAddIn.dll.config"
)

Write-Host "=== BigHand / Power Query Compatibility Fix ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify source DLL exists
Write-Host "Step 1: Checking Power Query DLL..." -ForegroundColor Yellow
if (!(Test-Path $sourceDll)) {
    Write-Host "ERROR: Power Query DLL not found at:" -ForegroundColor Red
    Write-Host "  $sourceDll" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check your Power Query installation path and update the script." -ForegroundColor Red
    exit 1
}

$sourceVersion = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($sourceDll).FileVersion
Write-Host "  Found Power Query DLL: v$sourceVersion" -ForegroundColor Green

# Step 2: Backup existing BigHand DLL
Write-Host ""
Write-Host "Step 2: Backing up BigHand DLL..." -ForegroundColor Yellow
if (Test-Path $targetDll) {
    $targetVersion = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($targetDll).FileVersion
    Write-Host "  Current BigHand DLL: v$targetVersion" -ForegroundColor White
    Copy-Item $targetDll $backupDll -Force
    Write-Host "  Backup created: $backupDll" -ForegroundColor Green
} else {
    Write-Host "  No existing DLL to backup" -ForegroundColor Yellow
}

# Step 3: Copy Power Query DLL to BigHand folder
Write-Host ""
Write-Host "Step 3: Copying Power Query DLL to BigHand folder..." -ForegroundColor Yellow
Copy-Item $sourceDll $targetDll -Force
Write-Host "  DLL copied successfully" -ForegroundColor Green

# Step 4: Update config files
Write-Host ""
Write-Host "Step 4: Updating binding redirects in config files..." -ForegroundColor Yellow

foreach ($configFile in $configFiles) {
    $configPath = Join-Path $bigHandPath $configFile

    if (!(Test-Path $configPath)) {
        Write-Host "  Skipping (not found): $configFile" -ForegroundColor Gray
        continue
    }

    Write-Host "  Updating: $configFile" -ForegroundColor White

    # Backup config
    $configBackup = "$configPath.bak"
    Copy-Item $configPath $configBackup -Force

    # Read and update config
    $content = Get-Content $configPath -Raw

    # Update the System.Diagnostics.DiagnosticSource binding redirect
    # Change newVersion="6.0.0.0" to newVersion="6.0.0.1" for this specific assembly
    $pattern = '(<assemblyIdentity\s+name="System\.Diagnostics\.DiagnosticSource"[^/]*/>\s*<bindingRedirect\s+oldVersion="[^"]*"\s+newVersion=")6\.0\.0\.0(")'
    $replacement = '${1}6.0.0.1${2}'

    $newContent = $content -replace $pattern, $replacement

    if ($newContent -ne $content) {
        Set-Content $configPath $newContent -NoNewline
        Write-Host "    Updated binding redirect to 6.0.0.1" -ForegroundColor Green
    } else {
        # Try alternative pattern (attributes in different order)
        $pattern2 = '(<assemblyIdentity\s+name="System\.Diagnostics\.DiagnosticSource"[^>]*>\s*</assemblyIdentity>\s*<bindingRedirect[^>]*newVersion=")6\.0\.0\.0(")'
        $newContent = $content -replace $pattern2, $replacement

        if ($newContent -ne $content) {
            Set-Content $configPath $newContent -NoNewline
            Write-Host "    Updated binding redirect to 6.0.0.1" -ForegroundColor Green
        } else {
            Write-Host "    No DiagnosticSource redirect found or already updated" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "=== Fix Applied ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Close Excel completely" -ForegroundColor White
Write-Host "2. Reopen Excel" -ForegroundColor White
Write-Host "3. Test that the BigHand ribbon appears" -ForegroundColor White
Write-Host "4. Test that Power Query works (Data > Get Data)" -ForegroundColor White
Write-Host ""
Write-Host "If it doesn't work, restore backups with:" -ForegroundColor Yellow
Write-Host "  Copy-Item '$backupDll' '$targetDll' -Force" -ForegroundColor Gray
Write-Host ""
