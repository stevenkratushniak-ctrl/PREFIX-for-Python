$ErrorActionPreference = "Stop"

$demoRoot = Join-Path $env:TEMP "prefix-python-final-demo"
$receiptDir = Join-Path $demoRoot "receipts"
$fixPath = Join-Path $demoRoot "broken_missing_colon.py"
$refusalPath = Join-Path $demoRoot "broken_return_outside_function.py"

New-Item -ItemType Directory -Force -Path $demoRoot | Out-Null
New-Item -ItemType Directory -Force -Path $receiptDir | Out-Null

[System.IO.File]::WriteAllText($fixPath, "if ready`nprint('launch')`n", [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($refusalPath, "return 1`n", [System.Text.UTF8Encoding]::new($false))

Write-Host "== Deterministic fix =="
python -m prefix_python $fixPath --apply --receipt-dir $receiptDir --json

$receiptPath = Get-ChildItem -Path $receiptDir -Filter *.json |
    Sort-Object Name |
    Select-Object -First 1 -ExpandProperty FullName

Write-Host "`n== Refusal =="
python -m prefix_python $refusalPath --json

Write-Host "`n== Receipt inspection =="
python -m prefix_python --inspect-receipt $receiptPath --json

Write-Host "`n== Replay verification =="
python -m prefix_python --replay-receipt $receiptPath --json
