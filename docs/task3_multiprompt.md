# Task3 Multi-Prompt and Multi-Model Strategy

Task3 is scored by Accuracy, so exact original-line recall matters more than fluent explanation.

## Multi-Prompt Run

Run three prompt variants with the same model, then merge by slot-level voting:

```bash
cd /root/autodl-tmp/ccl2026-poetry-eval
git pull
MODEL=/root/autodl-tmp/models/Qwen2.5-7B-Instruct bash scripts/run_task3_multiprompt_hf.sh
```

Output:

```text
outputs/submissions/submission_qwen2.5-7b-instruct_task3mp.json
```

The script creates:

```text
prompts/task3.txt
prompts/task3_direct.txt
prompts/task3_cloze.txt
```

and merges their task3 answers into:

```text
outputs/submissions/task3_qwen2.5-7b-instruct-task3-mp.json
```

## Multi-Model Merge

If another 10B-or-smaller open model is available, run only task3 with that model and then merge JSON files.

Example:

```bash
TASK3_FILES="\
outputs/submissions/task3_qwen2.5-7b-instruct-task3-mp.json \
outputs/submissions/task3_other-open-7b-task3.json" \
MERGE_RUN_NAME=task3-multimodel \
bash scripts/merge_task3_candidates.sh
```

Output:

```text
outputs/submissions/submission_qwen2.5-7b-instruct_task3-multimodel.json
```

## Merge Rule

- Each blank is merged independently.
- Repeated answers across prompt/model outputs win by majority.
- Ties are resolved by input order, so put the most trusted task3 JSON first.
- Empty, unknown, null-like answers are ignored.
- The final list length follows the official submission template.

This is not RAG: it does not retrieve external documents or add a knowledge base. It only combines model-generated answers.
