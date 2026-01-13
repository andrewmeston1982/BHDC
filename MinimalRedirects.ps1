# MinimalRedirects.ps1 - Remove binding redirects that might conflict with Power Query
# Theory: Power Query doesn't ship System.Text.Json or Microsoft.Bcl.AsyncInterfaces
# Having BigHand's redirects load these may poison the process for Power Query

$ErrorActionPreference = "Stop"

$bigHandPath = "C:\Program Files\BigHand\BigHand Document Creation"

# These assemblies exist in BigHand but NOT in Power Query
# Remove their binding redirects so they don't get loaded into the default context
$removeRedirects = @(
    "System.Text.Json",
    "Microsoft.Bcl.AsyncInterfaces"
)

Write-Host "=== Minimal Redirects Fix ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Removing redirects for assemblies not in Power Query:" -ForegroundColor Yellow
$removeRedirects | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
Write-Host ""

$configFiles = Get-ChildItem "$bigHandPath\*.config" | Where-Object { $_.Name -match "Iphelion.*\.config$" }

foreach ($configFile in $configFiles) {
    Write-Host "Processing: $($configFile.Name)" -ForegroundColor Cyan

    # Backup
    $backup = "$($configFile.FullName).bak2"
    Copy-Item $configFile.FullName $backup -Force

    [xml]$xml = Get-Content $configFile.FullName
    $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
    $ns.AddNamespace("asm", "urn:schemas-microsoft-com:asm.v1")

    $runtime = $xml.SelectSingleNode("//asm:assemblyBinding", $ns)

    if ($runtime) {
        $toRemove = @()

        $deps = $xml.SelectNodes("//asm:dependentAssembly", $ns)
        foreach ($dep in $deps) {
            $identity = $dep.SelectSingleNode("asm:assemblyIdentity", $ns)
            if ($identity) {
                $name = $identity.GetAttribute("name")
                if ($removeRedirects -contains $name) {
                    $toRemove += $dep
                    Write-Host "  Removing redirect: $name" -ForegroundColor Yellow
                }
            }
        }

        foreach ($node in $toRemove) {
            $node.ParentNode.RemoveChild($node) | Out-Null
        }

        $xml.Save($configFile.FullName)
        Write-Host "  Saved" -ForegroundColor Green
    }

    Write-Host ""
}

# Also remove the DLLs themselves so they don't get loaded
Write-Host "Removing DLLs from BigHand folder:" -ForegroundColor Yellow
foreach ($name in $removeRedirects) {
    $dll = Join-Path $bigHandPath "$name.dll"
    if (Test-Path $dll) {
        $backup = "$dll.disabled"
        Move-Item $dll $backup -Force
        Write-Host "  Disabled: $name.dll" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test: Open Excel, try Power Query, then try BigHand" -ForegroundColor White
Write-Host ""
Write-Host "If BigHand breaks, restore with:" -ForegroundColor Gray
Write-Host '  Get-ChildItem "C:\Program Files\BigHand\BigHand Document Creation\*.disabled" | Rename-Item -NewName { $_.Name -replace "\.disabled$","" }' -ForegroundColor Gray
Write-Host '  Get-ChildItem "C:\Program Files\BigHand\BigHand Document Creation\*.bak2" | ForEach-Object { Copy-Item $_.FullName ($_.FullName -replace "\.bak2$","") -Force }' -ForegroundColor Gray
