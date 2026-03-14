"""
backend/models_registry/llm_registry.py
Modular LLM loader. Add new providers by extending PROVIDER_MAP.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_core.language_models import BaseLanguageModel

from backend.core.config import settings


# ─────────────────────────────────────────────────────────────────────────────
#  Provider loaders
# ─────────────────────────────────────────────────────────────────────────────

def _load_gemma() -> BaseLanguageModel:
    """Load Gemma-3 via HuggingFace transformers pipeline wrapped in LangChain."""
    from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig
    import torch

    model_path = str(settings.gemma_model_path)

    # 4-bit quantization config matching your working local setup
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        local_files_only=True,
        quantization_config=bnb_config,
        device_map="cuda:0",
    )
    model.eval()

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=500,
        do_sample=False,
        pad_token_id=0,
        eos_token_id=1,
        # apply_chat_template is handled automatically by the pipeline
        # when the tokenizer has a chat_template defined
    )
    return HuggingFacePipeline(pipeline=pipe)


def _load_openai() -> BaseLanguageModel:
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
    )


def _load_mistral() -> BaseLanguageModel:
    """Mistral via HuggingFace – set MISTRAL_MODEL_PATH in .env."""
    from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    import os
    path = os.getenv("MISTRAL_MODEL_PATH", "./models/LLM/Mistral-7B-Instruct")
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        path, torch_dtype=torch.float16, device_map="auto", load_in_4bit=True,
        local_files_only=True,
    )
    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer,
                    max_new_tokens=512, temperature=0.2, do_sample=True)
    return HuggingFacePipeline(pipeline=pipe)


def _load_llama() -> BaseLanguageModel:
    """LLaMA-3 via HuggingFace – set LLAMA_MODEL_PATH in .env."""
    from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    import os
    path = os.getenv("LLAMA_MODEL_PATH", "./models/LLM/Meta-Llama-3-8B-Instruct")
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        path, torch_dtype=torch.float16, device_map="auto", load_in_4bit=True,
        local_files_only=True,
    )
    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer,
                    max_new_tokens=512, temperature=0.2, do_sample=True)
    return HuggingFacePipeline(pipeline=pipe)


PROVIDER_MAP: dict[str, Any] = {
    "gemma": _load_gemma,
    "openai": _load_openai,
    "mistral": _load_mistral,
    "llama": _load_llama,
}


@lru_cache(maxsize=1)
def get_llm() -> BaseLanguageModel:
    """Return singleton LLM for the configured provider."""
    provider = settings.llm_provider
    loader = PROVIDER_MAP.get(provider)
    if loader is None:
        raise ValueError(f"Unknown LLM provider: {provider}. "
                         f"Choose from {list(PROVIDER_MAP)}")
    return loader()
