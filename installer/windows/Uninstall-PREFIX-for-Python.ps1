[CmdletBinding()]
param([string]$InstallRoot = "", [string]$CodeCli = "")
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Invoke-VSCode.ps1")
if (-not $InstallRoot) {
    $InstallRoot = if ($env:PREFIX_INSTALL_ROOT) { $env:PREFIX_INSTALL_ROOT } else { Join-Path $env:LOCALAPPDATA "FastIndustries\PREFIX for Python" }
}
$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
if ($CodeCli) {
    $resolvedCode = $CodeCli
} elseif ($env:PREFIX_VSCODE_CLI) {
    $resolvedCode = $env:PREFIX_VSCODE_CLI
} else {
    $resolvedCode = (Get-Command code.cmd -ErrorAction SilentlyContinue | Select-Object -First 1).Source
}
if ($resolvedCode) {
    $args = @("--uninstall-extension", "fastindustries.prefix-python")
    if ($env:PREFIX_VSCODE_EXTENSIONS_DIR) { $args += @("--extensions-dir", $env:PREFIX_VSCODE_EXTENSIONS_DIR) }
    if ($env:PREFIX_VSCODE_USER_DATA_DIR) { $args += @("--user-data-dir", $env:PREFIX_VSCODE_USER_DATA_DIR) }
    $result = Invoke-PrefixVSCode $resolvedCode $args
    $result.Output | Out-Host
    if ($result.ExitCode -ne 0) { throw "VS Code extension removal failed with exit code $($result.ExitCode). The engine was not removed." }
}
if (Test-Path -LiteralPath $InstallRoot) {
    Remove-Item -LiteralPath $InstallRoot -Recurse -Force
}
Write-Host "PREFIX for Python was removed from $InstallRoot" -ForegroundColor Green
