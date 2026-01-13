// PatchAssemblies.cs - Run with: csc PatchAssemblies.cs /r:Mono.Cecil.dll && PatchAssemblies.exe
// Or in PowerShell: Add-Type -Path "Mono.Cecil.dll"; then run this as a script

using System;
using System.IO;
using Mono.Cecil;

class Program
{
    static void Main(string[] args)
    {
        string basePath = @"C:\Program Files\BigHand\BigHand Document Creation";

        // Target version that Power Query can work with (4.0.4.1 is common)
        var targetUnsafeVersion = new Version(4, 0, 4, 1);
        var targetMemoryVersion = new Version(4, 0, 1, 1);

        string[] dllsToCheck = new[]
        {
            "Iphelion.Outline.Controls.dll",
            "Iphelion.Outline.Integration.WorkSite.dll",
            "Iphelion.Outline.ExcelAddIn.dll",
            "Iphelion.Outline.Core.dll",
            "Iphelion.Outline.AddIn.dll"
        };

        foreach (var dllName in dllsToCheck)
        {
            string dllPath = Path.Combine(basePath, dllName);
            if (!File.Exists(dllPath))
            {
                Console.WriteLine($"Not found: {dllName}");
                continue;
            }

            Console.WriteLine($"\n=== {dllName} ===");

            try
            {
                // Read without resolving dependencies
                var resolver = new DefaultAssemblyResolver();
                resolver.AddSearchDirectory(basePath);

                var readerParams = new ReaderParameters
                {
                    AssemblyResolver = resolver,
                    ReadWrite = false
                };

                using (var assembly = AssemblyDefinition.ReadAssembly(dllPath, readerParams))
                {
                    bool modified = false;

                    foreach (var reference in assembly.MainModule.AssemblyReferences)
                    {
                        if (reference.Name == "System.Runtime.CompilerServices.Unsafe")
                        {
                            Console.WriteLine($"  Found: {reference.Name} v{reference.Version}");
                            // Uncomment to patch:
                            // reference.Version = targetUnsafeVersion;
                            // modified = true;
                        }
                        else if (reference.Name == "System.Memory")
                        {
                            Console.WriteLine($"  Found: {reference.Name} v{reference.Version}");
                        }
                        else if (reference.Name == "System.Text.Json")
                        {
                            Console.WriteLine($"  Found: {reference.Name} v{reference.Version}");
                        }
                        else if (reference.Name == "Microsoft.Bcl.AsyncInterfaces")
                        {
                            Console.WriteLine($"  Found: {reference.Name} v{reference.Version}");
                        }
                    }

                    // To actually patch, uncomment the modification lines above and:
                    // if (modified)
                    // {
                    //     string backupPath = dllPath + ".backup";
                    //     File.Copy(dllPath, backupPath, true);
                    //     assembly.Write(dllPath);
                    //     Console.WriteLine($"  PATCHED! Backup at {backupPath}");
                    // }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"  Error: {ex.Message}");
            }
        }

        Console.WriteLine("\nDone. Press any key to exit.");
        Console.ReadKey();
    }
}
