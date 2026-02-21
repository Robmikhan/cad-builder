"""
LLM orchestrator is optional.
If you set LLM_PROVIDER and LLM_API_KEY, you can:
- ask minimal clarifying measurement questions
- repair invalid CAD scripts automatically
- critique/simplify CAD for manufacturability

This repo ships with stubs to keep it vendor-neutral.
"""
import os

def enabled() -> bool:
    return os.getenv("LLM_PROVIDER", "none").lower() != "none"
