# VerifyAndLog.ps1 - Run as Administrator
# Verifies current state and enables assembly binding logging

$ErrorActionPreference = "Stop"

$bigHandPath = "C:\Program Files\BigHand\BigHand Document Creation"
$powerQueryPath = "C:\Program Files\Microsoft Office\root\Office16\ADDINS\Microsoft Power Query for Excel Integrated\bin"
$cecilPath = Join-Path $bigHandPath "Mono.Cecil.dll"
$logPath = "C:\FusionLogs"

Add-Type -Path $cecilPath

$targetAssemblies = @(
    "System.Runtime.CompilerServices.Unsafe",
    "System.Memory",
    "System.Text.Json",
    "Microsoft.Bcl.AsyncInterfaces",
    "System.Diagnostics.DiagnosticSource",
    "System.Buffers",
    "System.Numerics.Vectors"
)

Write-Host "=== VERIFICATION REPORT ===" -ForegroundColor Cyan
Write-Host ""

# Section 1: Compare DLL versions
Write-Host "1. DLL VERSION COMPARISON" -ForegroundColor Yellow
Write-Host "   (BigHand vs Power Query)" -ForegroundColor Gray
Write-Host ""
Write-Host ("{0,-45} {1,-15} {2,-15} {3}" -f "Assembly", "BigHand", "PowerQuery", "Match?") -ForegroundColor White
Write-Host ("{0,-45} {1,-15} {2,-15} {3}" -f "--------", "-------", "----------", "------") -ForegroundColor Gray

foreach ($name in $targetAssemblies) {
    $bhDll = Join-Path $bigHandPath "$name.dll"
    $pqDll = Join-Path $powerQueryPath "$name.dll"

    $bhVersion = "-"
    $pqVersion = "-"

    if (Test-Path $bhDll) {
        try {
            $asm = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($bhDll)
            $bhVersion = $asm.Name.Version.ToString()
            $asm.Dispose()
        } catch { $bhVersion = "ERROR" }
    }

    if (Test-Path $pqDll) {
        try {
            $asm = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($pqDll)
            $pqVersion = $asm.Name.Version.ToString()
            $asm.Dispose()
        } catch { $pqVersion = "ERROR" }
    }

    $match = if ($bhVersion -eq $pqVersion -and $bhVersion -ne "-") { "YES" } else { "NO" }
    $color = if ($match -eq "YES") { "Green" } else { "Red" }

    Write-Host ("{0,-45} {1,-15} {2,-15} " -f $name, $bhVersion, $pqVersion) -NoNewline
    Write-Host $match -ForegroundColor $color
}

Write-Host ""

# Section 2: Check binding redirects in config
Write-Host "2. BINDING REDIRECTS IN CONFIG" -ForegroundColor Yellow
Write-Host ""

$configFile = Join-Path $bigHandPath "Iphelion.Outline.ExcelAddIn.dll.config"
if (Test-Path $configFile) {
    [xml]$xml = Get-Content $configFile
    $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
    $ns.AddNamespace("asm", "urn:schemas-microsoft-com:asm.v1")

    $deps = $xml.SelectNodes("//asm:dependentAssembly", $ns)

    Write-Host ("{0,-45} {1,-20} {2}" -f "Assembly", "Redirects To", "In Target List?") -ForegroundColor White
    Write-Host ("{0,-45} {1,-20} {2}" -f "--------", "------------", "---------------") -ForegroundColor Gray

    foreach ($dep in $deps) {
        $identity = $dep.SelectSingleNode("asm:assemblyIdentity", $ns)
        $redirect = $dep.SelectSingleNode("asm:bindingRedirect", $ns)

        if ($identity -and $redirect) {
            $asmName = $identity.GetAttribute("name")
            $newVer = $redirect.GetAttribute("newVersion")
            $inList = if ($targetAssemblies -contains $asmName) { "YES" } else { "-" }

            Write-Host ("{0,-45} {1,-20} {2}" -f $asmName, $newVer, $inList)
        }
    }
} else {
    Write-Host "  Config file not found!" -ForegroundColor Red
}

Write-Host ""

# Section 3: Registry check
Write-Host "3. BIGHAND REGISTRY SETTINGS" -ForegroundColor Yellow
Write-Host ""

$regPaths = @(
    "HKCU:\Software\Microsoft\Office\Excel\Addins\Iphelion.Outline.ExcelAddIn",
    "HKLM:\Software\Microsoft\Office\Excel\Addins\Iphelion.Outline.ExcelAddIn",
    "HKLM:\Software\WOW6432Node\Microsoft\Office\Excel\Addins\Iphelion.Outline.ExcelAddIn"
)

foreach ($regPath in $regPaths) {
    if (Test-Path $regPath) {
        $props = Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue
        Write-Host "  $regPath" -ForegroundColor Green
        Write-Host "    LoadBehavior: $($props.LoadBehavior) (3=auto-load, 0=disabled)" -ForegroundColor White
    } else {
        Write-Host "  $regPath" -ForegroundColor Gray
        Write-Host "    (not found)" -ForegroundColor Gray
    }
}

Write-Host ""

# Section 4: Enable Fusion Logging
Write-Host "4. ENABLE ASSEMBLY BINDING LOGGING (Fusion Log)" -ForegroundColor Yellow
Write-Host ""

$enableLogging = Read-Host "Enable assembly binding logging? This logs ALL .NET assembly loads. (y/n)"

if ($enableLogging -eq 'y') {
    # Create log directory
    if (!(Test-Path $logPath)) {
        New-Item -ItemType Directory -Path $logPath -Force | Out-Null
    }

    # Enable fusion logging via registry
    $fusionKey = "HKLM:\SOFTWARE\Microsoft\Fusion"

    if (!(Test-Path $fusionKey)) {
        New-Item -Path $fusionKey -Force | Out-Null
    }

    Set-ItemProperty -Path $fusionKey -Name "LogPath" -Value $logPath
    Set-ItemProperty -Path $fusionKey -Name "ForceLog" -Value 1 -Type DWord
    Set-ItemProperty -Path $fusionKey -Name "LogFailures" -Value 1 -Type DWord
    Set-ItemProperty -Path $fusionKey -Name "LogResourceBinds" -Value 1 -Type DWord
    Set-ItemProperty -Path $fusionKey -Name "EnableLog" -Value 1 -Type DWord

    Write-Host ""
    Write-Host "  Fusion logging ENABLED" -ForegroundColor Green
    Write-Host "  Log location: $logPath" -ForegroundColor White
    Write-Host ""
    Write-Host "  NEXT STEPS:" -ForegroundColor Yellow
    Write-Host "  1. Close ALL Excel instances" -ForegroundColor White
    Write-Host "  2. Open Excel and trigger the Power Query error" -ForegroundColor White
    Write-Host "  3. Close Excel" -ForegroundColor White
    Write-Host "  4. Check $logPath for log files" -ForegroundColor White
    Write-Host "  5. Look for 'EXCEL.EXE' folder and any 'ERR' entries" -ForegroundColor White
    Write-Host ""
    Write-Host "  To DISABLE logging later, run:" -ForegroundColor Gray
    Write-Host "  Remove-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Fusion' -Name 'EnableLog'" -ForegroundColor Gray

} else {
    Write-Host "  Logging not enabled." -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== END OF REPORT ===" -ForegroundColor Cyan
Write-Host ""
