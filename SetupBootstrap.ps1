# SetupBootstrap.ps1 - Creates a clean VBA bootstrap for Power Query + BigHand
# Run as Administrator

$ErrorActionPreference = "Stop"

$bigHandPath = "C:\Program Files\BigHand\BigHand Document Creation"
$xlStartPath = [Environment]::GetFolderPath("ApplicationData") + "\Microsoft\Excel\XLSTART"

Write-Host "=== BigHand Bootstrap Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Disable BigHand auto-load
Write-Host "Step 1: Disabling BigHand auto-start..." -ForegroundColor Yellow

$regPaths = @(
    "HKCU:\Software\Microsoft\Office\Excel\Addins\Iphelion.Outline.ExcelAddIn",
    "HKLM:\Software\Microsoft\Office\Excel\Addins\Iphelion.Outline.ExcelAddIn"
)

foreach ($regPath in $regPaths) {
    if (Test-Path $regPath) {
        Set-ItemProperty -Path $regPath -Name "LoadBehavior" -Value 0
        Write-Host "  Set LoadBehavior=0 at $regPath" -ForegroundColor Green
    }
}

Write-Host ""

# Step 2: Ensure XLSTART exists
if (!(Test-Path $xlStartPath)) {
    New-Item -ItemType Directory -Path $xlStartPath -Force | Out-Null
}

Write-Host "Step 2: XLSTART folder: $xlStartPath" -ForegroundColor Yellow
Write-Host ""

# Step 3: Create the bootstrap VBA code
Write-Host "Step 3: VBA Code for Bootstrap Add-in" -ForegroundColor Yellow
Write-Host ""
Write-Host "Create a new Excel file, press Alt+F11, insert a Module, paste this code:" -ForegroundColor White
Write-Host ""
Write-Host "============ COPY START ============" -ForegroundColor Magenta

$vbaCode = @'
Option Explicit
Private Declare PtrSafe Sub Sleep Lib "kernel32" (ByVal ms As LongPtr)

Sub Auto_Open()
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False

    On Error Resume Next

    ' Create minimal query to force Power Query to load
    Dim wb As Workbook
    Set wb = Application.ActiveWorkbook
    If wb Is Nothing Then Set wb = Application.Workbooks.Add

    ' Add a blank query - this loads PQ assemblies
    Dim q As WorkbookQuery
    Set q = wb.Queries.Add("_init", "let x = 1 in x")

    ' Tiny delay for PQ to fully initialize
    Sleep 200

    ' Delete the query
    q.Delete

    ' Enable BigHand
    Dim addin As COMAddIn
    For Each addin In Application.COMAddIns
        If InStr(1, addin.ProgId, "Iphelion.Outline.ExcelAddIn", vbTextCompare) > 0 Then
            addin.Connect = True
            Exit For
        End If
    Next addin

    On Error GoTo 0

    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
End Sub
'@

Write-Host $vbaCode -ForegroundColor Cyan
Write-Host ""
Write-Host "============ COPY END ============" -ForegroundColor Magenta
Write-Host ""
Write-Host "Then save as:" -ForegroundColor White
Write-Host "  File > Save As" -ForegroundColor White
Write-Host "  Type: Excel Add-in (*.xlam)" -ForegroundColor White
Write-Host "  Location: $xlStartPath" -ForegroundColor Green
Write-Host "  Name: PQBootstrap.xlam" -ForegroundColor White
Write-Host ""
Write-Host "Close Excel completely and reopen." -ForegroundColor Yellow
Write-Host "Both Power Query and BigHand should work." -ForegroundColor Yellow
Write-Host ""
