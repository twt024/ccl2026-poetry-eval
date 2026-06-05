param(
  [string]$Model = "qwen2.5-7b-instruct",
  [string]$BaseUrl = "http://127.0.0.1:1234/v1"
)

$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "src"
$env:LOCAL_LLM_BASE_URL = $BaseUrl
$tasks = @("task1", "task2", "task3", "task4")
$runName = $Model -replace "[^A-Za-z0-9_.-]", "_"

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
    --output "outputs/raw/${task}_${runName}.jsonl" `
    --prompt "prompts/$task.txt" `
    --backend local_api `
    --model $Model `
    --temperature 0 `
    --max-new-tokens 768 `
    --resume

  Invoke-Python -m ccl_poetry_eval.postprocess `
    --task $task `
    --input "outputs/raw/${task}_${runName}.jsonl" `
    --output "outputs/submissions/${task}_${runName}.json" `
    --template auto
}

Invoke-Python -m ccl_poetry_eval.submit `
  --task1 "outputs/submissions/task1_${runName}.json" `
  --task2 "outputs/submissions/task2_${runName}.json" `
  --task3 "outputs/submissions/task3_${runName}.json" `
  --task4 "outputs/submissions/task4_${runName}.json" `
  --output "outputs/submissions/submission_${runName}.json"

Invoke-Python -m ccl_poetry_eval.validate_submission `
  --submission "outputs/submissions/submission_${runName}.json" `
  --template auto
