function Invoke-PrefixVSCode([string]$Executable, [string[]]$Arguments) {
    # Native stderr may contain warnings even on success. Bind the result to the
    # actual exit code, then let the caller independently check extension state.
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $global:LASTEXITCODE = $null
        $output = @(& $Executable @Arguments 2>&1)
        $exitCode = $global:LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($null -eq $exitCode) { throw 'VS Code did not report a native process exit code.' }
    return [pscustomobject]@{ ExitCode = [int]$exitCode; Output = @($output | ForEach-Object { $_.ToString() }) }
}
