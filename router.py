from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx

from config import PROVIDER_KEYS
from providers import PROVIDERS


@dataclass(frozen=True)
class Route:
    provider: str
    model: str


def _configured(provider: str) -> bool:
    return bool(PROVIDER_KEYS.get(PROVIDERS[provider]["key_name"]))


def load_routes(model: str, preferred: str | None = None) -> list[Route]:
    routes: list[Route] = []
    if preferred and preferred in PROVIDERS and _configured(preferred):
        routes.append(Route(preferred, model))

    for provider in ("openrouter", "groq", "cerebras", "gemini", "mistral", "deepseek", "huggingface", "openai", "bazaarlink", "ollama"):
        if provider in PROVIDERS and _configured(provider):
            route = Route(provider, model)
            if route not in routes:
                routes.append(route)
    return routes


async def chat_with_fallback(
    model: str,
    messages: list[dict[str, Any]],
    preferred_provider: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    failures: list[str] = []
    for route in load_routes(model, preferred_provider):
        try:
            return await _request(route, messages, stream=False, **kwargs)
        except (httpx.HTTPError, RuntimeError, ValueError) as exc:
            failures.append(f"{route.provider}: {exc}")
    if not failures:
        raise RuntimeError("No configured providers are available")
    raise RuntimeError("All configured providers failed: " + " | ".join(failures))


async def stream_with_fallback(
    model: str,
    messages: list[dict[str, Any]],
    preferred_provider: str | None = None,
    **kwargs: Any,
) -> tuple[Route, AsyncIterator[bytes]]:
    failures: list[str] = []
    for route in load_routes(model, preferred_provider):
        try:
            return route, await _request(route, messages, stream=True, **kwargs)
        except (httpx.HTTPError, RuntimeError, ValueError) as exc:
            failures.append(f"{route.provider}: {exc}")
    raise RuntimeError("All configured providers failed: " + " | ".join(failures))


async def _request(
    route: Route,
    messages: list[dict[str, Any]],
    stream: bool,
    **kwargs: Any,
) -> Any:
    provider = PROVIDERS[route.provider]
    key = PROVIDER_KEYS[provider["key_name"]]
    payload = {"model": route.model, "messages": messages, **kwargs}
    if stream:
        payload["stream"] = True

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if route.provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/wallacethomas538-glitch/free-llm-gateway"
        headers["X-Title"] = "VektorFlow Free LLM Gateway"

    client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=20.0))

    if stream:
        request = client.build_request(
            "POST",
            f'{provider["base_url"]}/chat/completions',
            json=payload,
            headers=headers,
        )
        response = await client.send(request, stream=True)
        if response.status_code >= 400:
            body = await response.aread()
            await response.aclose()
            await client.aclose()
            raise RuntimeError(
                f"{route.provider} returned HTTP {response.status_code}: "
                f"{body[:1000].decode(errors='replace')}"
            )

        async def iterator() -> AsyncIterator[bytes]:
            try:
                async for chunk in response.aiter_raw():
                    if chunk:
                        yield chunk
            finally:
                await response.aclose()
                await client.aclose()

        return iterator()

    try:
        response = await client.post(
            f'{provider["base_url"]}/chat/completions',
            json=payload,
            headers=headers,
        )
    finally:
        await client.aclose()

    if response.status_code >= 400:
        raise RuntimeError(
            f"{route.provider} returned HTTP {response.status_code}: {response.text[:1000]}"
        )
    return response.json()
