from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class ModelClient(Protocol):
    def generate(self, prompt: str) -> str:
        """Return raw model text for one prompt."""


@dataclass
class DummyClient:
    task: str

    def generate(self, prompt: str) -> str:
        if self.task == "task1":
            return '{"ans_qa_words": {}, "ans_qa_sents": {}, "choose_id": "A"}'
        if self.task == "task2":
            return '{"flag": 0, "answer": ""}'
        if self.task == "task3":
            return '{"answer": []}'
        if self.task == "task4":
            return '{"answer": "A"}'
        return '{"answer": ""}'


class LocalAPIClient:
    """Small OpenAI-compatible client for local open-source model servers."""

    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.0,
        max_new_tokens: int = 512,
        timeout: int = 300,
    ) -> None:
        self.model = model
        self.base_url = (base_url or os.getenv("LOCAL_LLM_BASE_URL") or "").rstrip("/")
        if not self.base_url:
            raise ValueError(
                "Missing local API base URL. Set LOCAL_LLM_BASE_URL or pass --base-url."
            )
        self.api_key = api_key or os.getenv("LOCAL_LLM_API_KEY")
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_new_tokens,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Local API request failed: {exc}") from exc

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"Local API response has no choices: {data}")
        first = choices[0]
        message = first.get("message") or {}
        return message.get("content") or first.get("text") or ""


class HFClient:
    def __init__(
        self,
        model: str,
        temperature: float = 0.0,
        max_new_tokens: int = 512,
        torch_dtype: str = "auto",
    ) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "HuggingFace backend requires: python -m pip install -e \".[hf]\""
            ) from exc

        self.torch = torch
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model,
            device_map="auto",
            torch_dtype=torch_dtype,
            trust_remote_code=True,
        )
        self.model.eval()

    def generate(self, prompt: str) -> str:
        input_text = self._format_chat(prompt)
        inputs = self.tokenizer(input_text, return_tensors="pt").to(self.model.device)
        do_sample = self.temperature > 0
        generation_kwargs = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": do_sample,
            "pad_token_id": self.tokenizer.eos_token_id,
        }
        if do_sample:
            generation_kwargs["temperature"] = self.temperature

        with self.torch.inference_mode():
            output_ids = self.model.generate(**inputs, **generation_kwargs)
        new_tokens = output_ids[0][inputs["input_ids"].shape[-1] :]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    def _format_chat(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        try:
            return self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        except Exception:
            return prompt


def build_client(
    backend: str,
    model: str,
    task: str,
    temperature: float,
    max_new_tokens: int,
    base_url: str | None = None,
) -> ModelClient:
    if backend == "dummy":
        return DummyClient(task=task)
    if backend == "local_api":
        return LocalAPIClient(
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
        )
    if backend == "hf":
        return HFClient(
            model=model,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
        )
    raise ValueError(f"Unsupported backend: {backend}")
