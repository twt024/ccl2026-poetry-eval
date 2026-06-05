$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "src"
$tasks = @("task1", "task2", "task3", "task4")

function Invoke-Python {
  & python @args
  if ($LASTEXITCODE -ne 0) {
    throw "python command failed with exit code $LASTEXITCODE"
  }
}

foreach ($task in $tasks) {
  Invoke-Python -m ccl_poetry_eval.infer `
    --task $task `
    --input "CCPA2026-test_data/$task.json" `
    --output "outputs/raw/${task}_dummy.jsonl" `
    --prompt "prompts/$task.txt" `
    --backend dummy `
    --model dummy

  Invoke-Python -m ccl_poetry_eval.postprocess `
    --task $task `
    --input "outputs/raw/${task}_dummy.jsonl" `
    --output "outputs/submissions/${task}_dummy.json" `
    --template auto
}

Invoke-Python -m ccl_poetry_eval.submit `
  --task1 "outputs/submissions/task1_dummy.json" `
  --task2 "outputs/submissions/task2_dummy.json" `
  --task3 "outputs/submissions/task3_dummy.json" `
  --task4 "outputs/submissions/task4_dummy.json" `
  --output "outputs/submissions/submission_dummy.json"

Invoke-Python -m ccl_poetry_eval.validate_submission `
  --submission "outputs/submissions/submission_dummy.json" `
  --template auto
