[CmdletBinding()]
param(
    [string]$InstallRoot = "",
    [string]$CodeCli = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
Add-Type -AssemblyName System.IO.Compression.FileSystem

$ProductVersion = "0.1.0"
$ExtensionId = "fastindustries.prefix-python"
$BundleRoot = $PSScriptRoot
$PayloadRoot = Join-Path $BundleRoot "payload"
$ManifestPath = Join-Path $PayloadRoot "payload-manifest.json"

function Stop-Install([string]$Message) {
    throw "PREFIX for Python installation blocked: $Message"
}

function Resolve-CodeCli([string]$Requested) {
    $candidates = @()
    if ($Requested) { $candidates += $Requested }
    if ($env:PREFIX_VSCODE_CLI) { $candidates += $env:PREFIX_VSCODE_CLI }
    $fromPath = Get-Command code.cmd -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($fromPath) { $candidates += $fromPath.Source }
    if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code\bin\code.cmd") }
    if ($env:ProgramFiles) { $candidates += (Join-Path $env:ProgramFiles "Microsoft VS Code\bin\code.cmd") }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return (Get-Item -LiteralPath $candidate).FullName
        }
    }
    return $null
}

if (-not [Environment]::Is64BitOperatingSystem) {
    Stop-Install "Windows x64 is required. This operating system is not 64-bit."
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    Stop-Install "the package payload manifest is missing. Re-download the complete Windows x64 package."
}

$ResolvedCodeCli = Resolve-CodeCli $CodeCli
if (-not $ResolvedCodeCli) {
    Stop-Install "Visual Studio Code was not found. Install the x64 stable build from https://code.visualstudio.com/ and run this installer again."
}

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
if ($Manifest.product -ne "PREFIX for Python" -or $Manifest.version -ne $ProductVersion -or $Manifest.platform -ne "windows-x64") {
    Stop-Install "the package manifest identity is invalid."
}
foreach ($artifact in $Manifest.artifacts) {
    $artifactPath = Join-Path $PayloadRoot ([string]$artifact.name)
    if (-not (Test-Path -LiteralPath $artifactPath -PathType Leaf)) {
        Stop-Install "required payload '$($artifact.name)' is missing."
    }
    $actualHash = (Get-FileHash -LiteralPath $artifactPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne [string]$artifact.sha256) {
        Stop-Install "payload '$($artifact.name)' failed SHA-256 verification."
    }
}

if (-not $InstallRoot) {
    if ($env:PREFIX_INSTALL_ROOT) {
        $InstallRoot = $env:PREFIX_INSTALL_ROOT
    } elseif ($env:LOCALAPPDATA) {
        $InstallRoot = Join-Path $env:LOCALAPPDATA "FastIndustries\PREFIX for Python"
    } else {
        Stop-Install "LOCALAPPDATA is unavailable, so a per-user installation location cannot be selected."
    }
}
$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
$InstallParent = Split-Path -Parent $InstallRoot
$StageRoot = Join-Path $InstallParent ("PREFIX for Python.installing." + $PID)
$BackupRoot = Join-Path $InstallParent ("PREFIX for Python.previous." + $PID)
$RuntimeRoot = Join-Path $StageRoot "runtime"
$SitePackages = Join-Path $RuntimeRoot "Lib\site-packages"
$SwapComplete = $false

$PythonArchive = Join-Path $PayloadRoot ([string]$Manifest.runtime.archive)
$Wheel = Join-Path $PayloadRoot ([string]$Manifest.wheel)
$Vsix = Join-Path $PayloadRoot ([string]$Manifest.vsix)

try {
    New-Item -ItemType Directory -Path $InstallParent -Force | Out-Null
    if (Test-Path -LiteralPath $StageRoot) { Remove-Item -LiteralPath $StageRoot -Recurse -Force }
    if (Test-Path -LiteralPath $BackupRoot) { Remove-Item -LiteralPath $BackupRoot -Recurse -Force }
    New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null
    [IO.Compression.ZipFile]::ExtractToDirectory($PythonArchive, $RuntimeRoot)

    $Python = Join-Path $RuntimeRoot "python.exe"
    $Pth = Join-Path $RuntimeRoot "python312._pth"
    if (-not (Test-Path -LiteralPath $Python -PathType Leaf) -or -not (Test-Path -LiteralPath $Pth -PathType Leaf)) {
        Stop-Install "the bundled CPython 3.12 runtime is incomplete."
    }
    @("python312.zip", ".", "Lib\site-packages", "import site") | Set-Content -LiteralPath $Pth -Encoding Ascii
    New-Item -ItemType Directory -Path $SitePackages -Force | Out-Null
    [IO.Compression.ZipFile]::ExtractToDirectory($Wheel, $SitePackages)

    $Assets = Join-Path $StageRoot "assets"
    New-Item -ItemType Directory -Path $Assets -Force | Out-Null
    Copy-Item -LiteralPath $Vsix -Destination (Join-Path $Assets (Split-Path -Leaf $Vsix))
    Copy-Item -LiteralPath (Join-Path $PayloadRoot "broken_missing_colon.txt") -Destination (Join-Path $Assets "broken_missing_colon.txt")
    Copy-Item -LiteralPath (Join-Path $PayloadRoot "broken_return_outside_function.txt") -Destination (Join-Path $Assets "broken_return_outside_function.txt")

    $BinRoot = Join-Path $StageRoot "bin"
    New-Item -ItemType Directory -Path $BinRoot -Force | Out-Null
    "@echo off`r`n`"%~dp0..\runtime\python.exe`" -m prefix_python %*`r`n" | Set-Content -LiteralPath (Join-Path $BinRoot "prefix-python.cmd") -Encoding Ascii
    "@echo off`r`n`"%~dp0..\runtime\python.exe`" -m prefix_python.operator_console %*`r`n" | Set-Content -LiteralPath (Join-Path $BinRoot "prefix-python-ops.cmd") -Encoding Ascii

    $versionOutput = & $Python -m prefix_python --version 2>&1
    if ($LASTEXITCODE -ne 0 -or $versionOutput -notmatch "0\.1\.0") {
        Stop-Install "the bundled engine version smoke check failed: $versionOutput"
    }
    $smokeOutput = "if ready`nprint('launch')`n" | & $Python -m prefix_python --stdin --json 2>&1
    if ($LASTEXITCODE -ne 0) { Stop-Install "the correction smoke check failed: $smokeOutput" }
    $smoke = $smokeOutput | ConvertFrom-Json
    if ($smoke.status -ne "ACCEPT_FIXED" -or $smoke.source -notmatch "if ready:") {
        Stop-Install "the correction smoke check returned an unexpected result."
    }

    $installRecord = [ordered]@{
        product = "PREFIX for Python"
        version = $ProductVersion
        platform = "windows-x64"
        runtime = "CPython $(& $Python -c 'import platform; print(platform.python_version())')"
        runtime_path = (Join-Path $InstallRoot "runtime\python.exe")
        extension_id = $ExtensionId
        wheel_sha256 = (Get-FileHash -LiteralPath $Wheel -Algorithm SHA256).Hash.ToLowerInvariant()
        vsix_sha256 = (Get-FileHash -LiteralPath $Vsix -Algorithm SHA256).Hash.ToLowerInvariant()
        smoke_status = $smoke.status
    }
    $installRecord | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $StageRoot "install-manifest.json") -Encoding UTF8

    if (Test-Path -LiteralPath $InstallRoot) { Move-Item -LiteralPath $InstallRoot -Destination $BackupRoot }
    Move-Item -LiteralPath $StageRoot -Destination $InstallRoot
    $SwapComplete = $true

    $CodeArgs = @("--install-extension", (Join-Path $InstallRoot "assets\prefix-python-0.1.0.vsix"), "--force")
    if ($env:PREFIX_VSCODE_EXTENSIONS_DIR) { $CodeArgs += @("--extensions-dir", $env:PREFIX_VSCODE_EXTENSIONS_DIR) }
    if ($env:PREFIX_VSCODE_USER_DATA_DIR) { $CodeArgs += @("--user-data-dir", $env:PREFIX_VSCODE_USER_DATA_DIR) }
    $codeOutput = & $ResolvedCodeCli @CodeArgs 2>&1
    if ($LASTEXITCODE -ne 0) { Stop-Install "VS Code extension installation failed: $codeOutput" }
    $ListArgs = @("--list-extensions")
    if ($env:PREFIX_VSCODE_EXTENSIONS_DIR) { $ListArgs += @("--extensions-dir", $env:PREFIX_VSCODE_EXTENSIONS_DIR) }
    if ($env:PREFIX_VSCODE_USER_DATA_DIR) { $ListArgs += @("--user-data-dir", $env:PREFIX_VSCODE_USER_DATA_DIR) }
    $installedExtensions = & $ResolvedCodeCli @ListArgs 2>&1
    if ($LASTEXITCODE -ne 0 -or -not ($installedExtensions -match "(?m)^fastindustries\.prefix-python$")) {
        Stop-Install "VS Code did not report the installed PREFIX extension after setup: $installedExtensions"
    }

    $finalPython = Join-Path $InstallRoot "runtime\python.exe"
    $finalSmoke = "if ready`nprint('restart proof')`n" | & $finalPython -m prefix_python --stdin --json 2>&1 | ConvertFrom-Json
    if ($finalSmoke.status -ne "ACCEPT_FIXED") { Stop-Install "the installed-engine restart smoke check failed." }
    if (Test-Path -LiteralPath $BackupRoot) { Remove-Item -LiteralPath $BackupRoot -Recurse -Force }

    Write-Host "PREFIX for Python $ProductVersion is installed." -ForegroundColor Green
    Write-Host "VS Code extension: $ExtensionId" -ForegroundColor Green
    Write-Host "Engine: $finalPython" -ForegroundColor Green
    Write-Host "Open a Python file in VS Code and use 'PREFIX: Govern Active Python Transition'." -ForegroundColor Cyan
    exit 0
} catch {
    if ($SwapComplete) {
        if (Test-Path -LiteralPath $InstallRoot) { Remove-Item -LiteralPath $InstallRoot -Recurse -Force }
        if (Test-Path -LiteralPath $BackupRoot) { Move-Item -LiteralPath $BackupRoot -Destination $InstallRoot }
    } elseif ((-not (Test-Path -LiteralPath $InstallRoot)) -and (Test-Path -LiteralPath $BackupRoot)) {
        Move-Item -LiteralPath $BackupRoot -Destination $InstallRoot
    }
    if (Test-Path -LiteralPath $StageRoot) { Remove-Item -LiteralPath $StageRoot -Recurse -Force }
    Write-Error $_
    exit 1
}
