# CreateDelayedLoader.ps1 - Run as Administrator
# Disables BigHand at startup and creates a macro to auto-enable it after Power Query loads

$ErrorActionPreference = "Stop"

Write-Host "=== BigHand Delayed Loader Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Disable BigHand COM add-in from auto-loading
Write-Host "Step 1: Disabling BigHand auto-start in registry..." -ForegroundColor Yellow

$regPaths = @(
    "HKCU:\Software\Microsoft\Office\Excel\Addins\Iphelion.Outline.ExcelAddIn",
    "HKLM:\Software\Microsoft\Office\Excel\Addins\Iphelion.Outline.ExcelAddIn",
    "HKLM:\Software\WOW6432Node\Microsoft\Office\Excel\Addins\Iphelion.Outline.ExcelAddIn"
)

foreach ($regPath in $regPaths) {
    if (Test-Path $regPath) {
        # LoadBehavior: 3 = Load at startup, 2 = Load on demand, 0 = Disabled
        $current = Get-ItemProperty -Path $regPath -Name "LoadBehavior" -ErrorAction SilentlyContinue
        if ($current) {
            Write-Host "  Found: $regPath" -ForegroundColor Green
            Write-Host "  Current LoadBehavior: $($current.LoadBehavior)" -ForegroundColor Gray
            Set-ItemProperty -Path $regPath -Name "LoadBehavior" -Value 0
            Write-Host "  Set LoadBehavior to 0 (disabled)" -ForegroundColor Yellow
        }
    }
}

Write-Host ""

# Step 2: Create XLSTART folder path
$xlStartPath = [Environment]::GetFolderPath("ApplicationData") + "\Microsoft\Excel\XLSTART"
if (!(Test-Path $xlStartPath)) {
    New-Item -ItemType Directory -Path $xlStartPath -Force | Out-Null
}

Write-Host "Step 2: XLSTART location: $xlStartPath" -ForegroundColor Yellow
Write-Host ""

# Step 3: Instructions for creating the loader
Write-Host "Step 3: Create the auto-loader add-in" -ForegroundColor Yellow
Write-Host ""
Write-Host "MANUAL STEPS REQUIRED:" -ForegroundColor Red
Write-Host "======================" -ForegroundColor Red
Write-Host ""
Write-Host "1. Open Excel (BigHand should NOT load now)" -ForegroundColor White
Write-Host ""
Write-Host "2. Press Alt+F11 to open VBA Editor" -ForegroundColor White
Write-Host ""
Write-Host "3. In VBA Editor: Insert menu > Module" -ForegroundColor White
Write-Host ""
Write-Host "4. Paste this EXACT code:" -ForegroundColor White
Write-Host ""
Write-Host "========== COPY FROM HERE ==========" -ForegroundColor Magenta

$vbaCode = @'
Option Explicit

Private Declare PtrSafe Sub Sleep Lib "kernel32" (ByVal ms As LongPtr)

Sub Auto_Open()
    ' Force Power Query assemblies to load first
    On Error Resume Next
    Dim dummy As Long
    dummy = Application.ActiveWorkbook.Queries.Count
    On Error GoTo 0

    ' Small delay to ensure PQ is fully initialized
    Sleep 500

    ' Now enable BigHand
    EnableBigHand
End Sub

Sub EnableBigHand()
    Dim addin As COMAddIn
    On Error Resume Next

    For Each addin In Application.COMAddIns
        If InStr(1, addin.ProgId, "Iphelion.Outline.ExcelAddIn", vbTextCompare) > 0 Then
            If Not addin.Connect Then
                addin.Connect = True
            End If
            Exit For
        End If
    Next addin

    On Error GoTo 0
End Sub
'@

Write-Host $vbaCode -ForegroundColor Cyan
Write-Host ""
Write-Host "========== COPY TO HERE ==========" -ForegroundColor Magenta
Write-Host ""
Write-Host "5. File > Save As:" -ForegroundColor White
Write-Host "   - Save as type: Excel Add-in (*.xlam)" -ForegroundColor White
Write-Host "   - Location: $xlStartPath" -ForegroundColor Green
Write-Host "   - Filename: BigHandLoader.xlam" -ForegroundColor White
Write-Host ""
Write-Host "6. Close and reopen Excel" -ForegroundColor White
Write-Host ""
Write-Host "7. Test Power Query first, then check if BigHand ribbon appears" -ForegroundColor White
Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "What this does:" -ForegroundColor Gray
Write-Host "- BigHand no longer auto-loads at startup" -ForegroundColor Gray
Write-Host "- The XLAM runs Auto_Open which:" -ForegroundColor Gray
Write-Host "  1. Touches Queries collection (loads PQ assemblies)" -ForegroundColor Gray
Write-Host "  2. Waits 500ms" -ForegroundColor Gray
Write-Host "  3. Programmatically enables BigHand add-in" -ForegroundColor Gray
Write-Host ""
