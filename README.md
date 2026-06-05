# CCL2026 中文古诗词赏析评测 baseline

这是一个面向第二届中文古诗词赏析评测的合规 baseline 工程，目标是先跑通：

```text
读取官方 JSON 数据 -> 调用 10B 及以下开源模型 -> 生成 task1-task4 答案 -> 后处理 -> 生成提交 JSON -> 写技术报告
```

## 合规边界

- 不使用 RAG，不接入向量库、搜索引擎或外部知识库。
- 不使用闭源模型。
- 模型规模控制在 10B 及以下。
- 技术报告必须提交，报告模板在 `reports/tech_report.md`。

## 目录

```text
ccl2026-poetry-eval/
  configs/              # 运行配置
  data/
    raw/                # 官方训练集、验证集、测试集，默认不提交到 git
    processed/          # 清洗或切分后的数据
  prompts/              # 四个任务的 prompt
  src/ccl_poetry_eval/  # 推理、后处理、评测、提交脚本
  outputs/
    raw/                # 模型原始输出 jsonl
    submissions/        # 后处理后的提交文件
    logs/               # 日志
  reports/              # 技术报告
```

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[hf,metrics]"
```

如果只想先看流程，不加载大模型，可以不装 `hf` 额外依赖，直接用 `dummy` 后端跑通脚本。

## 放置数据

你已经把官方数据解压在项目根目录，当前默认路径为：

```text
CCPA2026-train_data/task1.json
CCPA2026-train_data/task2.json
CCPA2026-train_data/task3.json
CCPA2026-train_data/task4.json
CCPA2026-test_data/task1.json
CCPA2026-test_data/task2.json
CCPA2026-test_data/task3.json
CCPA2026-test_data/task4.json
提交示例.json
```

这些数据文件已在 `.gitignore` 中忽略，避免误传到公开仓库。脚本支持 JSON list、JSONL，以及常见的 `{ "data": [...] }` 格式。

## 批量推理

先用 dummy 后端确认本地环境和数据结构：

```powershell
.\scripts\run_dummy.ps1
```

### 方式一：HuggingFace 本地加载

```powershell
python -m ccl_poetry_eval.infer `
  --task task4 `
  --input CCPA2026-test_data/task4.json `
  --output outputs/raw/task4_raw.jsonl `
  --backend hf `
  --model Qwen/Qwen2.5-7B-Instruct `
  --max-new-tokens 512 `
  --temperature 0
```

### 方式二：本地 OpenAI-compatible 服务

适合 LM Studio、vLLM、Ollama OpenAI-compatible API 等本地开源模型服务。

```powershell
$env:LOCAL_LLM_BASE_URL="http://127.0.0.1:1234/v1"

python -m ccl_poetry_eval.infer `
  --task task4 `
  --input CCPA2026-test_data/task4.json `
  --output outputs/raw/task4_raw.jsonl `
  --backend local_api `
  --model qwen2.5-7b-instruct `
  --max-new-tokens 512 `
  --temperature 0
```

也可以直接用一键脚本：

```powershell
.\scripts\run_local_api.ps1 -Model "qwen2.5-7b-instruct" -BaseUrl "http://127.0.0.1:1234/v1"
```

## 后处理

```powershell
python -m ccl_poetry_eval.postprocess `
  --task task4 `
  --input outputs/raw/task4_raw.jsonl `
  --output outputs/submissions/task4.json `
  --template 提交示例.json
```

建议始终传入 `--template 提交示例.json`。官方测试集和提交示例中存在个别字段文字不一致的情况，后处理会以提交示例的 key 为准。

## 生成总提交

```powershell
python -m ccl_poetry_eval.submit `
  --task1 outputs/submissions/task1.json `
  --task2 outputs/submissions/task2.json `
  --task3 outputs/submissions/task3.json `
  --task4 outputs/submissions/task4.json `
  --output outputs/submissions/submission.json
```

如果官方后续明确了不同提交格式，只需要调整 `src/ccl_poetry_eval/submit.py` 或 `postprocess.py` 的字段映射。

## 校验提交结构

生成最终提交后，可以和官方示例做结构校验：

```powershell
python -m ccl_poetry_eval.validate_submission `
  --submission outputs/submissions/submission.json `
  --template 提交示例.json
```

## 本地评估

```powershell
python -m ccl_poetry_eval.evaluate `
  --task task4 `
  --gold data/raw/task4_dev.json `
  --pred outputs/submissions/task4.json
```

当前评估脚本先提供 exact match、选项准确率、task2 flag 准确率和可选 BLEU。正式分数仍以官方平台为准。

## 推荐迭代节奏

1. 用 `dummy` 后端跑通全流程。
2. 用 7B/8B 开源指令模型跑 task4 这种选择题，确认输出格式稳定。
3. 再跑 task1/task2 的解释题，做后处理和 prompt 错误分析。
4. 切一部分训练集做 dev set，记录每次 prompt 或模型变更。
5. baseline 稳定后，再考虑 LoRA/QLoRA 微调。

## 云服务器运行

本地没有 NVIDIA 显卡时，把项目上传到 24GB 显存左右的 Ubuntu GPU 服务器，然后运行：

```bash
bash scripts/setup_autodl.sh
bash scripts/run_hf_qwen25_7b.sh
```

云端说明见 `docs/cloud_gpu.md`。当前默认模型是 `Qwen/Qwen2.5-7B-Instruct`。
