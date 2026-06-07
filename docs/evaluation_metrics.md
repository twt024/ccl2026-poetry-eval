# Evaluation Metrics and Optimization Strategy

This document is the project memory for scoring rules. All prompt, postprocess, and model-run decisions should follow these metric priorities.

## Final Score

```text
Score = (Task1_score + Task2_score + Task3_score + Task4_score) / 4
```

Task-level scores:

```text
Task1_score = (word_understanding + sentence_understanding + emotion_accuracy) / 3
Task2_score = allusion_identification
Task3_score = poetry_analogy_accuracy
Task4_score = poetry_analysis_accuracy
```

## Task1: Word, Sentence, Emotion

Subtasks:

```text
word_understanding = (BLEU + BERTScore) / 2
sentence_understanding = (BLEU + BERTScore) / 2
emotion_accuracy = Accuracy
```

Optimization implications:

- Word and sentence explanations should be short, literal, and close to reference wording.
- High BERTScore but low BLEU means the meaning is roughly right, but wording is too free.
- Do not write long appreciation-style answers for word and sentence explanations.
- Word explanations should look like dictionary glosses, usually 2-15 Chinese characters.
- Sentence explanations should be modern Chinese paraphrases, preferably one concise sentence.
- Emotion choice must be exactly A/B/C/D.

Priority for Task1:

```text
1. Keep meanings correct.
2. Shorten and standardize wording to lift BLEU.
3. Preserve emotion choice accuracy.
```

## Task2: Allusion Identification

Score:

```text
Task2_score = (flag_accuracy + BERTScore) / 2
```

Optimization implications:

- `flag` accuracy is as important as explanation quality.
- If `flag = 0`, answer is not compared, so false positives are costly.
- If `flag = 1`, the explanation should name the allusion and state its meaning in the poem.
- The prompt should be conservative: only mark clear historical, literary, mythological, or classical allusions as 1.

Priority for Task2:

```text
1. Avoid false positives and false negatives in flag.
2. For flag=1, give concise but complete allusion explanation.
3. Do not over-optimize unless Task2 becomes the bottleneck.
```

## Task3: Poetry Analogy / Fill-in-the-Blank

Score:

```text
Task3_score = Accuracy
```

Optimization implications:

- This is exact-answer oriented. Semantic similarity does not help.
- Answers should be original classical text, not paraphrase.
- Empty answers score zero; guessing is better than leaving blanks.
- Answer list length must match the number of blanks in the official template.
- Each blank should be a separate array element.
- Remove extra punctuation unless it is part of the expected text.

Priority for Task3:

```text
1. Force non-empty guesses.
2. Force list length to match template.
3. Improve memorization-style prompt with train-only few-shot examples.
4. Consider task-specific reruns, alternative models, or ensemble only after prompt/postprocess are stable.
```

Current project observation:

```text
Task3 is the main bottleneck.
Formatting fix improved Task3 from 0.2293 to 0.2569, but many answers were still empty.
Core issue is recall of original lines, not only JSON formatting.
```

## Task4: Poetry Analysis Multiple Choice

Score:

```text
Task4_score = Accuracy
```

Optimization implications:

- Only the final option A/B/C/D matters.
- The prompt must force the model to identify whether the question asks for correct or incorrect option.
- Many errors come from selecting the most plausible option when the question asks for the incorrect one.
- The model should check content, emotion, technique, allusion, structure, and notes.

Priority for Task4:

```text
1. Identify the question direction: correct vs incorrect.
2. Compare each option with poem text and notes.
3. Output only A/B/C/D.
```

## Experiment Rules

Use these rules unless the user explicitly decides otherwise:

- Prefer one-task-at-a-time experiments when diagnosing prompt changes.
- If running all tasks together, delete old raw outputs first because scripts use `--resume`.
- Do not change Task2 casually because it is currently the strongest task.
- Prioritize Task3 first, then Task4, then Task1, then Task2.
- Always validate submission schema before upload.

Useful validation command:

```bash
python -m ccl_poetry_eval.validate_submission \
  --submission outputs/submissions/submission_qwen2.5-7b-instruct（4）.json \
  --template auto
```
