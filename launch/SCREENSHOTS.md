# Screenshot Plan

## 1. Hero Surface

- Open `site/index.html`
- Capture the hero, proof bar, and headline
- Goal: category-defining first impression

## 2. Before and After Code

- Show `examples/broken_missing_colon.txt`
- Show the corrected output from `py -3.12 -m prefix_python examples\broken_missing_colon.txt --json`
- Goal: immediate proof of deterministic correction

## 3. Refusal Surface

- Run `py -3.12 -m prefix_python examples\broken_return_outside_function.txt --json`
- Capture the refusal reason
- Goal: show refusal semantics, not overreach

## 4. VS Code Enter Surface

- Open a Python file with a missing block colon
- Press Enter and capture the immediate lawful correction
- Goal: prove that PREFIX prefixes correction at the structural boundary instead of waiting for a later repair command

## 5. Engine JSON Output

- Capture the canonical JSON with `status`, `events`, `legality_report`, and `proof_trace`
- Goal: infrastructure-grade output with visible deterministic proof

## 6. Receipt Inspection Surface

- Run `py -3.12 -m prefix_python --inspect-receipt <receipt>.json --json`
- Capture `lineage_id`, `chain_depth`, and `proof_trace`
- Goal: show that corrections are inspectable and auditable after the fact

## 7. Repo Layout

- Capture the top-level product structure from the README
- Goal: GitHub-ready clarity
