# Next Surface Candidates
Scores 1-5. A-G higher is better; H-J lower is better. Value=A+B+C+D+E+F+G+(6-H)+(6-I)+(6-J). Frequency is an engineering estimate, not telemetry.

|Candidate|A|B|C|D|E|F|G|H|I|J|Value|Decision|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
|Missing mandatory in in iteration clause|4|4|5|5|5|5|5|1|2|2|46|SELECT|
|Missing as in except/except* alias|2|3|5|5|5|5|5|1|2|2|43|SELECT|
|Unexpected/inconsistent dedent|4|5|4|4|2|2|5|4|5|3|32|reject APPLY: block association|
|Missing comma in containers/calls|5|4|3|3|1|2|4|4|5|3|28|reject: operators/colon/concatenation compete|
|Unterminated short string|5|4|4|4|2|3|5|3|4|2|34|reject: close/escape/triple/delete compete|
|Positional after keyword argument|4|4|5|5|1|2|5|4|5|3|34|ANALYZE only|
|Duplicate keyword argument|3|4|5|5|1|2|5|3|5|2|35|ANALYZE only|
|Non-default parameter after default|3|4|5|5|1|2|5|3|5|2|35|ANALYZE only|
|Missing as in with item|2|3|4|4|1|3|4|4|4|3|28|reject: comma can be lawful|
|Import alias missing as|3|3|5|5|1|3|5|3|4|2|36|reject: comma can be lawful|
|Conditional = typo|4|5|5|5|1|1|5|5|5|2|34|reject: == vs := intent|
|Leading-zero decimal|2|3|5|5|1|2|5|2|4|2|37|reject: decimal/base intent|

The selected pair wins because each exposes a mandatory grammar connector inside an identifiable construct and supports token-preserving insertion plus exhaustive candidate-cardinality proof.