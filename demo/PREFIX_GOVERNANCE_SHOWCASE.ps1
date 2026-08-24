$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$demoRoot = Join-Path $root "qualification\_hardening_artifacts\prefix_governance_showcase"
$receiptDir = Join-Path $demoRoot "receipts"
$applyPath = Join-Path $demoRoot "apply_missing_colon.py"
$rollbackPath = Join-Path $demoRoot "rollback_tab_normalization.py"
$reportPath = Join-Path $demoRoot "PREFIX_GOVERNANCE_SHOWCASE_REPORT.json"

if (Test-Path -LiteralPath $demoRoot) {
    Remove-Item -LiteralPath $demoRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $receiptDir | Out-Null

function Invoke-PrefixJsonFromText {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Source
    )
    $output = $Source | python -m prefix_python --stdin --json
    return ($output -join "`n") | ConvertFrom-Json
}

function Invoke-PrefixJsonFromFile {
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )
    $output = & python -m prefix_python @Arguments
    return ($output -join "`n") | ConvertFrom-Json
}

function Select-GovernanceEvidence {
    param(
        [Parameter(Mandatory = $true)]
        [object] $Result
    )
    return [ordered]@{
        state = $Result.state
        lane = $Result.lane
        status = $Result.status
        refusal_code = $Result.refusal_code
        governing_law = $Result.structural_context.governing_law
        surface_class = $Result.structural_context.surface_class
        locality = $Result.structural_context.locality
        continuation_count = $Result.continuation_graph.successor_count
        legality_score = $Result.legality_score.score
        mutation_performed = $Result.mutation_performed
        parse_reparse_validated = $Result.parse_reparse_validated
        transition_witness_root_sha256 = $Result.transition_governance.transition_witness_root_sha256
        continuation_graph_sha256 = $Result.continuation_graph.graph_sha256
        recommendation_packet_sha256 = $Result.recommendation_packet.packet_sha256
        ast_sha256 = $Result.ast_sha256
        token_sha256 = $Result.token_sha256
    }
}

[System.IO.File]::WriteAllText($applyPath, "if ready`nprint('governed')`n", [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($rollbackPath, "if ready:`n`tprint('rollback')`n", [System.Text.UTF8Encoding]::new($false))

$applyResult = Invoke-PrefixJsonFromFile -Arguments @($applyPath, "--apply", "--receipt-dir", $receiptDir, "--json")
$receiptPath = $applyResult.receipt_path
$inspectResult = Invoke-PrefixJsonFromFile -Arguments @("--inspect-receipt", $receiptPath, "--json")
$replayResult = Invoke-PrefixJsonFromFile -Arguments @("--replay-receipt", $receiptPath, "--json")
$rollbackApplyResult = Invoke-PrefixJsonFromFile -Arguments @($rollbackPath, "--apply", "--receipt-dir", $receiptDir, "--json")
$rollbackReceiptPath = $rollbackApplyResult.receipt_path
$rollbackInspectResult = Invoke-PrefixJsonFromFile -Arguments @("--inspect-receipt", $rollbackReceiptPath, "--json")
$rollbackResult = Invoke-PrefixJsonFromFile -Arguments @("--rollback", $rollbackReceiptPath, "--json")
$adviseResult = Invoke-PrefixJsonFromText -Source "elif ready:`n    print('bounded')`n"
$analyzeResult = Invoke-PrefixJsonFromText -Source "value =`n"
$refuseResult = Invoke-PrefixJsonFromText -Source "return 1`n"

$report = [ordered]@{
    demo_name = "PREFIX deterministic structural-governance showcase"
    root = $root
    apply = Select-GovernanceEvidence -Result $applyResult
    advise = Select-GovernanceEvidence -Result $adviseResult
    analyze = Select-GovernanceEvidence -Result $analyzeResult
    refuse = Select-GovernanceEvidence -Result $refuseResult
    receipt = [ordered]@{
        path = $receiptPath
        chain_depth = $inspectResult.chain_depth
        lineage_id = $inspectResult.lineage_id
        receipt_kind = $inspectResult.receipt_kind
        transition_sha256 = $inspectResult.proof_trace.transition_sha256
        rollback_ready = $inspectResult.proof_trace.rollback_ready
    }
    rollback = [ordered]@{
        apply_receipt = $rollbackReceiptPath
        rollback_ready = $rollbackInspectResult.proof_trace.rollback_ready
        rollback_status = $rollbackResult.status
        rollback_mutation_performed = $rollbackResult.mutation_performed
        rollback_receipt = $rollbackResult.receipt_path
        restored_sha256 = $rollbackResult.output_sha256
    }
    replay = [ordered]@{
        replay_verified = $replayResult.proof_trace.replay_verified
        stored_transition_sha256 = $replayResult.proof_trace.stored_transition_sha256
        replay_ast_sha256 = $replayResult.ast_sha256
        output_sha256 = $replayResult.output_sha256
        parse_reparse_validated = $replayResult.parse_reparse_validated
    }
    invariants = [ordered]@{
        advise_mutated = $adviseResult.mutation_performed
        analyze_mutated = $analyzeResult.mutation_performed
        refuse_mutated = $refuseResult.mutation_performed
        replay_mutated = $replayResult.mutation_performed
        apply_has_receipt = [bool]$receiptPath
        apply_witness_replayed = ($applyResult.output_sha256 -eq $replayResult.output_sha256)
        rollback_ready = $rollbackInspectResult.proof_trace.rollback_ready
        rollback_restored = ($rollbackResult.status -eq "ACCEPT_FIXED")
    }
}

$json = $report | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText($reportPath, $json + "`n", [System.Text.UTF8Encoding]::new($false))

Write-Host "PREFIX governance showcase complete"
Write-Host "Report: $reportPath"
Write-Host "Receipt: $receiptPath"
Write-Host "Apply witness: $($report.apply.transition_witness_root_sha256)"
Write-Host "Advise packet: $($report.advise.recommendation_packet_sha256)"
Write-Host "Rollback receipt: $($report.rollback.rollback_receipt)"
Write-Host "Replay verified: $($report.replay.replay_verified)"
