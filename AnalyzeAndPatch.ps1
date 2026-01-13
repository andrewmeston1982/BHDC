# AnalyzeAndPatch.ps1 - Run as Administrator
# First, just analyzes. Then can patch if uncommented.

$basePath = "C:\Program Files\BigHand\BigHand Document Creation"
$cecilPath = Join-Path $basePath "Mono.Cecil.dll"

# Load Mono.Cecil
Add-Type -Path $cecilPath

$dllsToCheck = @(
    "Iphelion.Outline.Controls.dll",
    "Iphelion.Outline.Integration.WorkSite.dll",
    "Iphelion.Outline.ExcelAddIn.dll",
    "Iphelion.Outline.Core.dll",
    "Iphelion.Outline.AddIn.dll",
    "Iphelion.Outline.Excel.dll",
    "Unity.Container.dll"
)

$problemAssemblies = @(
    "System.Runtime.CompilerServices.Unsafe",
    "System.Memory",
    "System.Text.Json",
    "Microsoft.Bcl.AsyncInterfaces",
    "System.Diagnostics.DiagnosticSource"
)

Write-Host "=== ANALYSIS MODE ===" -ForegroundColor Cyan
Write-Host "Scanning for problematic assembly references...`n"

foreach ($dllName in $dllsToCheck) {
    $dllPath = Join-Path $basePath $dllName

    if (!(Test-Path $dllPath)) {
        Write-Host "Not found: $dllName" -ForegroundColor Yellow
        continue
    }

    Write-Host "`n=== $dllName ===" -ForegroundColor Green

    try {
        $assembly = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($dllPath)

        foreach ($ref in $assembly.MainModule.AssemblyReferences) {
            if ($problemAssemblies -contains $ref.Name) {
                Write-Host "  $($ref.Name) v$($ref.Version)" -ForegroundColor Red
            }
        }

        $assembly.Dispose()
    }
    catch {
        Write-Host "  Error: $_" -ForegroundColor Red
    }
}

Write-Host "`n`n=== NEXT STEPS ===" -ForegroundColor Cyan
Write-Host "If you see version 6.0.0.0 or 5.0.0.0 references above,"
Write-Host "we may be able to patch them to 4.0.x versions."
Write-Host "`nTo patch, we'd need to know what version Power Query expects."
Write-Host "Check: C:\Program Files\Microsoft Office\root\Office16\ADDINS\Power Query\"
