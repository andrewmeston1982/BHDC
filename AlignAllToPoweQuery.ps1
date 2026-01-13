# AlignAllToPowerQuery.ps1 - Run as Administrator
# Restores BigHand originals, then aligns ALL binding redirects to Power Query versions

$ErrorActionPreference = "Stop"

$bigHandPath = "C:\Program Files\BigHand\BigHand Document Creation"
$powerQueryPath = "C:\Program Files\Microsoft Office\root\Office16\ADDINS\Microsoft Power Query for Excel Integrated\bin"
$cecilPath = Join-Path $bigHandPath "Mono.Cecil.dll"

Write-Host "=== Align BigHand to Power Query Versions ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Restore all .orig files first
Write-Host "Step 1: Restoring original BigHand files..." -ForegroundColor Yellow
$origFiles = Get-ChildItem "$bigHandPath\*.orig" -ErrorAction SilentlyContinue
foreach ($orig in $origFiles) {
    $targetName = $orig.FullName -replace '\.orig$', ''
    Copy-Item $orig.FullName $targetName -Force
    Write-Host "  Restored: $($orig.Name -replace '\.orig$','')" -ForegroundColor Green
}
if ($origFiles.Count -eq 0) {
    Write-Host "  No .orig files to restore" -ForegroundColor Gray
}
Write-Host ""

# Load Mono.Cecil
Add-Type -Path $cecilPath

# Assemblies we care about
$targetAssemblies = @(
    "System.Runtime.CompilerServices.Unsafe",
    "System.Memory",
    "System.Text.Json",
    "Microsoft.Bcl.AsyncInterfaces",
    "System.Diagnostics.DiagnosticSource",
    "System.Buffers",
    "System.Numerics.Vectors",
    "System.Text.Encodings.Web",
    "System.Threading.Tasks.Extensions",
    "System.ValueTuple"
)

# Step 2: Get Power Query assembly versions
Write-Host "Step 2: Reading Power Query assembly versions..." -ForegroundColor Yellow
$pqVersions = @{}

foreach ($name in $targetAssemblies) {
    $dllPath = Join-Path $powerQueryPath "$name.dll"
    if (Test-Path $dllPath) {
        try {
            $asm = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($dllPath)
            $pqVersions[$name] = $asm.Name.Version.ToString()
            Write-Host "  $name = $($pqVersions[$name])" -ForegroundColor Green
            $asm.Dispose()
        } catch {
            Write-Host "  $name = ERROR: $_" -ForegroundColor Red
        }
    }
}
Write-Host ""

# Step 3: Copy Power Query DLLs to BigHand
Write-Host "Step 3: Copying Power Query DLLs to BigHand folder..." -ForegroundColor Yellow
foreach ($name in $pqVersions.Keys) {
    $src = Join-Path $powerQueryPath "$name.dll"
    $dst = Join-Path $bigHandPath "$name.dll"
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "  Copied: $name.dll" -ForegroundColor Green
    }
}
Write-Host ""

# Step 4: Update config files with correct versions
Write-Host "Step 4: Updating binding redirects in config files..." -ForegroundColor Yellow

$configFiles = Get-ChildItem "$bigHandPath\*.config" | Where-Object { $_.Name -match "Iphelion.*\.config$" }

foreach ($configFile in $configFiles) {
    Write-Host "  Processing: $($configFile.Name)" -ForegroundColor Cyan

    [xml]$xml = Get-Content $configFile.FullName

    $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
    $ns.AddNamespace("asm", "urn:schemas-microsoft-com:asm.v1")

    $dependentAssemblies = $xml.SelectNodes("//asm:dependentAssembly", $ns)

    foreach ($dep in $dependentAssemblies) {
        $identity = $dep.SelectSingleNode("asm:assemblyIdentity", $ns)
        $redirect = $dep.SelectSingleNode("asm:bindingRedirect", $ns)

        if ($identity -and $redirect) {
            $asmName = $identity.GetAttribute("name")

            if ($pqVersions.ContainsKey($asmName)) {
                $pqVersion = $pqVersions[$asmName]
                $oldNew = $redirect.GetAttribute("newVersion")

                if ($oldNew -ne $pqVersion) {
                    # Update to Power Query's version
                    $redirect.SetAttribute("oldVersion", "0.0.0.0-$pqVersion")
                    $redirect.SetAttribute("newVersion", $pqVersion)
                    Write-Host "    $asmName : $oldNew -> $pqVersion" -ForegroundColor Yellow
                }
            }
        }
    }

    $xml.Save($configFile.FullName)
}

Write-Host ""
Write-Host "=== Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Restart Excel and test both BigHand and Power Query." -ForegroundColor White
Write-Host ""
