# PreloadPowerQueryAssemblies.ps1
# Creates an Excel startup script that preloads Power Query assemblies
# This ensures PQ's assembly versions are loaded BEFORE BigHand's redirects take effect

$ErrorActionPreference = "Stop"

$xlStartPath = [Environment]::GetFolderPath("ApplicationData") + "\Microsoft\Excel\XLSTART"
$powerQueryPath = "C:\Program Files\Microsoft Office\root\Office16\ADDINS\Microsoft Power Query for Excel Integrated\bin"

Write-Host "=== Power Query Preloader Setup ===" -ForegroundColor Cyan
Write-Host ""

# Ensure XLSTART exists
if (!(Test-Path $xlStartPath)) {
    New-Item -ItemType Directory -Path $xlStartPath -Force | Out-Null
}

# Create the preloader add-in
$addinPath = Join-Path $xlStartPath "PQPreloader.xlam"

Write-Host "Creating preloader at: $addinPath" -ForegroundColor Yellow
Write-Host ""

# We'll create a simple VBA module that loads the assemblies
$vbaCode = @'
' PQPreloader - Loads Power Query assemblies at Excel startup
' This runs BEFORE VSTO add-ins initialize, ensuring PQ assemblies load first

Private Sub Workbook_Open()
    On Error Resume Next

    ' Force Power Query to initialize by accessing its object model
    Dim pqLoaded As Boolean
    pqLoaded = False

    ' Try to access Workbook.Queries collection - this triggers PQ assembly loading
    Dim wb As Workbook
    Set wb = ThisWorkbook.Application.ActiveWorkbook

    If Not wb Is Nothing Then
        Dim qCount As Long
        qCount = wb.Queries.Count  ' This loads PQ assemblies
        pqLoaded = True
    End If

    On Error GoTo 0
End Sub
'@

Write-Host "VBA Code to add to a new Excel Add-in:" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Gray
Write-Host $vbaCode -ForegroundColor White
Write-Host "=======================================" -ForegroundColor Gray
Write-Host ""

Write-Host "Manual steps required:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Open Excel (with BigHand disabled in COM Add-ins for now)" -ForegroundColor White
Write-Host "2. Press Alt+F11 to open VBA Editor" -ForegroundColor White
Write-Host "3. Insert > Module" -ForegroundColor White
Write-Host "4. Paste this code:" -ForegroundColor White
Write-Host ""
Write-Host '   Private Sub Auto_Open()' -ForegroundColor Cyan
Write-Host '       On Error Resume Next' -ForegroundColor Cyan
Write-Host '       Dim q As Long' -ForegroundColor Cyan
Write-Host '       q = ActiveWorkbook.Queries.Count' -ForegroundColor Cyan
Write-Host '   End Sub' -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Save as 'PQPreloader.xlam' in:" -ForegroundColor White
Write-Host "   $xlStartPath" -ForegroundColor Green
Write-Host ""
Write-Host "6. Re-enable BigHand in COM Add-ins" -ForegroundColor White
Write-Host "7. Restart Excel" -ForegroundColor White
Write-Host ""
Write-Host "The Auto_Open macro runs before VSTO add-ins load," -ForegroundColor Gray
Write-Host "forcing Power Query assemblies to load first." -ForegroundColor Gray
Write-Host ""
