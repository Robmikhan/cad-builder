"""
Ollama HTTP client for local LLM inference.
Default model: qwen2.5-coder:7b (good at code generation, fits RTX 3060 12GB).
"""
from __future__ import annotations
import json
import logging
import os
from typing import Optional

import requests

_log = logging.getLogger(__name__)

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")


def is_available() -> bool:
    """Check if Ollama server is reachable."""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def generate(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    timeout: int = 120,
) -> str:
    """
    Call Ollama /api/generate and return the full response text.
    Raises RuntimeError if Ollama is not available or the request fails.
    """
    model = model or OLLAMA_MODEL
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if system:
        payload["system"] = system

    _log.info("Ollama generate: model=%s, prompt_len=%d", model, len(prompt))

    try:
        r = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json=payload,
            timeout=timeout,
        )
        r.raise_for_status()
    except requests.ConnectionError:
        raise RuntimeError(
            "Ollama not reachable. Start it with: ollama serve "
            "(or ensure the Ollama desktop app is running)."
        )
    except requests.HTTPError as e:
        raise RuntimeError(f"Ollama HTTP error: {e}")

    data = r.json()
    response = data.get("response", "")

    _log.info(
        "Ollama response: model=%s, tokens=%d, eval_duration=%.1fs",
        model,
        data.get("eval_count", 0),
        data.get("eval_duration", 0) / 1e9,
    )
    return response


def extract_code_block(text: str) -> str:
    """Extract the first ```python or ``` code block from LLM output."""
    lines = text.split("\n")
    in_block = False
    code_lines = []
    for line in lines:
        if line.strip().startswith("```") and not in_block:
            in_block = True
            continue
        if line.strip() == "```" and in_block:
            break
        if in_block:
            code_lines.append(line)
    if code_lines:
        return "\n".join(code_lines)
    # No code block found, return raw text stripped
    return text.strip()


def extract_json(text: str) -> dict:
    """Extract JSON from LLM output (handles code blocks and raw JSON)."""
    # Try to find JSON in code blocks first
    cleaned = extract_code_block(text)
    # If it looks like it starts with {, try to parse
    for candidate in [cleaned, text]:
        candidate = candidate.strip()
        # Find the first { and last }
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(candidate[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not extract JSON from LLM response: {text[:500]}")
