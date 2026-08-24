$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Workspace = Join-Path $Root "qualification\_hardening_artifacts\operator_console_demo"
$Bundle = Join-Path $Root "release\prefix-python-0.1.0-rc2.zip"

if (Test-Path $Workspace) {
    Remove-Item -LiteralPath $Workspace -Recurse -Force
}

$null = python -m prefix_python.operator_console init --root $Workspace --release-bundle $Bundle
$invite = python -m prefix_python.operator_console invite --root $Workspace --cohort-name "Founding Operator Cohort" --team-name "Northwind" --operator-name "Avery Lane" --operator-email "avery@northwind.dev" --seat-count 12 --start-date 2026-05-01 | ConvertFrom-Json
$null = python -m prefix_python.operator_console activate --root $Workspace --invite-id $invite.invite_id --activation-date 2026-05-01
$null = python -m prefix_python.operator_console checkpoint --root $Workspace --team-id $invite.team_id --checkpoint-date 2026-05-21 --onboarding complete --install complete --demo complete --replay complete --refusal complete --rollback complete --trust-level high --enterprise-interest active --replay-count 8 --refusal-count 3 --rollback-count 2 --open-issues 0 --notes "Deterministic workflow validated."
$null = python -m prefix_python.operator_console issue --root $Workspace --team-id $invite.team_id --issue-date 2026-05-18 --severity medium --category install --summary "Initial VSIX trust prompt required acknowledgement." --status resolved
$null = python -m prefix_python.operator_console cohort-summary --root $Workspace --as-of 2026-05-21
$null = python -m prefix_python.operator_console reminders --root $Workspace --as-of 2026-05-21
$null = python -m prefix_python.operator_console conversion-summary --root $Workspace --as-of 2026-05-21
$null = python -m prefix_python.operator_console distribution-manifest --root $Workspace --as-of 2026-05-21

$artifacts = @(
    (Join-Path $Workspace "program.json"),
    (Join-Path $Workspace ("invites\" + $invite.invite_id + ".json")),
    (Join-Path $Workspace ("enrollments\" + $invite.team_id + ".json")),
    (Join-Path $Workspace "reports\cohort-summary-2026-05-21.json"),
    (Join-Path $Workspace "reports\reminders-2026-05-21.json"),
    (Join-Path $Workspace "reports\conversion-summary-2026-05-21.json"),
    (Join-Path $Workspace "reports\distribution-manifest-2026-05-21.json")
)

foreach ($artifact in $artifacts) {
    if (-not (Test-Path $artifact)) {
        throw "Missing expected founding-operator demo artifact: $artifact"
    }
}

[pscustomobject]@{
    workspace = $Workspace
    invite_id = $invite.invite_id
    team_id = $invite.team_id
    evaluation_license_id = $invite.license_id
    bundle_sha256 = (Get-FileHash -Algorithm SHA256 $Bundle).Hash.ToLower()
    artifact_count = $artifacts.Count
} | ConvertTo-Json -Depth 4
