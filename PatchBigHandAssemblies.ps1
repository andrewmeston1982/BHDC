# PatchBigHandAssemblies.ps1 - Run as Administrator
# Patches BigHand assembly references to match Power Query versions using Mono.Cecil

$ErrorActionPreference = "Stop"

$bigHandPath = "C:\Program Files\BigHand\BigHand Document Creation"
$powerQueryPath = "C:\Program Files\Microsoft Office\root\Office16\ADDINS\Microsoft Power Query for Excel Integrated\bin"
$cecilPath = Join-Path $bigHandPath "Mono.Cecil.dll"

Write-Host "=== BigHand Assembly Patcher ===" -ForegroundColor Cyan
Write-Host ""

# Load Mono.Cecil
if (!(Test-Path $cecilPath)) {
    Write-Host "ERROR: Mono.Cecil.dll not found at $cecilPath" -ForegroundColor Red
    exit 1
}

Add-Type -Path $cecilPath

# Assemblies that conflict between BigHand and Power Query
$conflictAssemblies = @(
    "System.Runtime.CompilerServices.Unsafe",
    "System.Memory",
    "System.Text.Json",
    "Microsoft.Bcl.AsyncInterfaces",
    "System.Diagnostics.DiagnosticSource",
    "System.Buffers",
    "System.Numerics.Vectors"
)

# Step 1: Get Power Query's assembly versions
Write-Host "Step 1: Scanning Power Query assembly versions..." -ForegroundColor Yellow
$powerQueryVersions = @{}

foreach ($assemblyName in $conflictAssemblies) {
    $dllPath = Join-Path $powerQueryPath "$assemblyName.dll"
    if (Test-Path $dllPath) {
        try {
            $asm = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($dllPath)
            $version = $asm.Name.Version
            $publicKeyToken = [BitConverter]::ToString($asm.Name.PublicKeyToken).Replace("-", "").ToLower()
            $powerQueryVersions[$assemblyName] = @{
                Version = $version
                PublicKeyToken = $asm.Name.PublicKeyToken
            }
            Write-Host "  $assemblyName : v$version (token: $publicKeyToken)" -ForegroundColor Green
            $asm.Dispose()
        } catch {
            Write-Host "  $assemblyName : Error reading - $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  $assemblyName : Not found in Power Query" -ForegroundColor Gray
    }
}

Write-Host ""

# BigHand DLLs to patch
$dllsToPath = @(
    "Iphelion.Outline.Controls.dll",
    "Iphelion.Outline.Integration.WorkSite.dll",
    "Iphelion.Outline.ExcelAddIn.dll",
    "Iphelion.Outline.Core.dll",
    "Iphelion.Outline.AddIn.dll",
    "Iphelion.Outline.Excel.dll",
    "Iphelion.Outline.Model.dll",
    "Unity.Container.dll"
)

# Step 2: Patch BigHand assemblies
Write-Host "Step 2: Patching BigHand assemblies..." -ForegroundColor Yellow
Write-Host ""

foreach ($dllName in $dllsToPath) {
    $dllPath = Join-Path $bigHandPath $dllName

    if (!(Test-Path $dllPath)) {
        continue
    }

    Write-Host "Processing: $dllName" -ForegroundColor Cyan

    # Create backup
    $backupPath = "$dllPath.orig"
    if (!(Test-Path $backupPath)) {
        Copy-Item $dllPath $backupPath -Force
        Write-Host "  Backup created: $dllName.orig" -ForegroundColor Gray
    }

    try {
        # Read assembly with write capability
        $resolver = New-Object Mono.Cecil.DefaultAssemblyResolver
        $resolver.AddSearchDirectory($bigHandPath)
        $resolver.AddSearchDirectory($powerQueryPath)

        $readerParams = New-Object Mono.Cecil.ReaderParameters
        $readerParams.AssemblyResolver = $resolver
        $readerParams.ReadWrite = $false
        $readerParams.InMemory = $true

        $assembly = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($dllPath, $readerParams)
        $modified = $false

        foreach ($reference in $assembly.MainModule.AssemblyReferences) {
            if ($powerQueryVersions.ContainsKey($reference.Name)) {
                $pqInfo = $powerQueryVersions[$reference.Name]
                $oldVersion = $reference.Version
                $newVersion = $pqInfo.Version

                if ($oldVersion -ne $newVersion) {
                    Write-Host "  Patching: $($reference.Name) v$oldVersion -> v$newVersion" -ForegroundColor Yellow
                    $reference.Version = $newVersion

                    # Also update public key token if needed
                    if ($pqInfo.PublicKeyToken -and $pqInfo.PublicKeyToken.Length -gt 0) {
                        $reference.PublicKeyToken = $pqInfo.PublicKeyToken
                    }

                    $modified = $true
                }
            }
        }

        if ($modified) {
            # Write patched assembly
            $writerParams = New-Object Mono.Cecil.WriterParameters
            $assembly.Write($dllPath, $writerParams)
            Write-Host "  PATCHED successfully" -ForegroundColor Green
        } else {
            Write-Host "  No changes needed" -ForegroundColor Gray
        }

        $assembly.Dispose()
    }
    catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
    }

    Write-Host ""
}

# Step 3: Copy Power Query DLLs to BigHand folder
Write-Host "Step 3: Copying Power Query DLLs to BigHand folder..." -ForegroundColor Yellow

foreach ($assemblyName in $powerQueryVersions.Keys) {
    $sourceDll = Join-Path $powerQueryPath "$assemblyName.dll"
    $targetDll = Join-Path $bigHandPath "$assemblyName.dll"

    if (Test-Path $sourceDll) {
        # Backup existing if present
        if (Test-Path $targetDll) {
            $backupDll = "$targetDll.orig"
            if (!(Test-Path $backupDll)) {
                Copy-Item $targetDll $backupDll -Force
            }
        }

        Copy-Item $sourceDll $targetDll -Force
        Write-Host "  Copied: $assemblyName.dll" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=== Patching Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Close Excel completely" -ForegroundColor White
Write-Host "2. Reopen Excel" -ForegroundColor White
Write-Host "3. Test BigHand ribbon and Power Query" -ForegroundColor White
Write-Host ""
Write-Host "To restore originals, run:" -ForegroundColor Yellow
Write-Host '  Get-ChildItem "C:\Program Files\BigHand\BigHand Document Creation\*.orig" | ForEach-Object { Copy-Item $_.FullName ($_.FullName -replace "\.orig$","") -Force }' -ForegroundColor Gray
Write-Host ""
