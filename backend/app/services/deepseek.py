"""封装 DeepSeek 大模型调用（OpenAI 兼容接口，支持流式与非流式、模型与 Key 切换）。"""
import json
from typing import AsyncIterator, List

import httpx

from app.config import (
    ALLOWED_MODELS,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
)
from app.schemas import ChatMessage


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _payload(
    model: str,
    messages: List[ChatMessage],
    temperature: float,
    max_tokens: int,
    stream: bool,
) -> dict:
    return {
        "model": model,
        "messages": [m.model_dump() for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
        # 关闭思考模式：回复更直接、避免产生 reasoning_content。
        "thinking": {"type": "disabled"},
    }


def _resolve_model(model: str | None) -> str:
    """仅允许白名单内的模型，否则回退默认模型。"""
    return model if model in ALLOWED_MODELS else DEEPSEEK_MODEL


def _candidate_keys(api_key: str | None) -> list:
    """候选 Key 列表：优先自定义 Key，无效时回退默认 Key。"""
    custom = (api_key or "").strip()
    if custom and custom != DEEPSEEK_API_KEY:
        return [custom, DEEPSEEK_API_KEY]
    return [DEEPSEEK_API_KEY]


def _is_auth_error(exc: httpx.HTTPStatusError) -> bool:
    return exc.response.status_code in (401, 403)


async def chat_completion(
    messages: List[ChatMessage],
    temperature: float = 0.7,
    max_tokens: int = 2048,
    model: str | None = None,
    api_key: str | None = None,
) -> str:
    """非流式调用，一次性返回完整回复。"""
    model = _resolve_model(model)
    keys = _candidate_keys(api_key)
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, key in enumerate(keys):
            try:
                resp = await client.post(
                    f"{DEEPSEEK_BASE_URL}/chat/completions",
                    headers=_headers(key),
                    json=_payload(model, messages, temperature, max_tokens, stream=False),
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as exc:
                if _is_auth_error(exc) and i < len(keys) - 1:
                    continue  # 自定义 Key 无效，回退默认 Key 重试
                raise
    raise RuntimeError("无法调用大模型")  # 理论上不可达


async def _stream_once(
    client: httpx.AsyncClient,
    model: str,
    api_key: str,
    messages: List[ChatMessage],
    temperature: float,
    max_tokens: int,
) -> AsyncIterator[str]:
    async with client.stream(
        "POST",
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        headers=_headers(api_key),
        json=_payload(model, messages, temperature, max_tokens, stream=True),
    ) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line or not line.startswith("data:"):
                continue
            payload = line[len("data:"):].strip()
            if payload == "[DONE]":
                break
            try:
                chunk = json.loads(payload)
            except json.JSONDecodeError:
                continue
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            content = delta.get("content")
            if content:
                yield content


async def chat_completion_stream(
    messages: List[ChatMessage],
    temperature: float = 0.7,
    max_tokens: int = 2048,
    model: str | None = None,
    api_key: str | None = None,
) -> AsyncIterator[str]:
    """流式调用，逐个产出文本增量（token）。"""
    model = _resolve_model(model)
    keys = _candidate_keys(api_key)
    async with httpx.AsyncClient(timeout=120.0) as client:
        for i, key in enumerate(keys):
            try:
                async for token in _stream_once(
                    client, model, key, messages, temperature, max_tokens
                ):
                    yield token
                return
            except httpx.HTTPStatusError as exc:
                if _is_auth_error(exc) and i < len(keys) - 1:
                    continue  # 自定义 Key 无效，回退默认 Key 重试
                raise
