from typing import Any

import httpx

from config import BAZAARLINK_BASE_URL, PROVIDER_KEYS


PROVIDERS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "key_name": "openai",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_name": "groq",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_name": "openrouter",
    },
    "huggingface": {
        "base_url": "https://router.huggingface.co/v1",
        "key_name": "huggingface",
    },
    "bazaarlink": {
        "base_url": BAZAARLINK_BASE_URL,
        "key_name": "bazaarlink",
    },
}


def available_providers() -> list[str]:
    return [
        name
        for name, config in PROVIDERS.items()
        if PROVIDER_KEYS.get(config["key_name"])
    ]


def resolve_provider(provider: str | None) -> dict[str, Any]:
    name = (provider or "openrouter").lower()

    if name not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {name}")

    key_name = PROVIDERS[name]["key_name"]
    api_key = PROVIDER_KEYS.get(key_name)

    if not api_key:
        raise ValueError(f"Provider '{name}' is not configured")

    return {
        "name": name,
        "base_url": PROVIDERS[name]["base_url"],
        "api_key": api_key,
    }


async def chat_completion(
    provider: str,
    model: str,
    messages: list[dict[str, Any]],
    **kwargs: Any,
) -> dict[str, Any]:

    config = resolve_provider(provider)

    payload = {
        "model": model,
        "messages": messages,
        **kwargs,
    }

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/wallacethomas538-glitch/free-llm-gateway"
        headers["X-Title"] = "VektorFlow Free LLM Gateway"

    url = f"{config['base_url']}/chat/completions"

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            url,
            json=payload,
            headers=headers,
        )

    if response.status_code >= 400:
        raise RuntimeError(
            f"{provider} returned HTTP {response.status_code}: "
            f"{response.text[:1000]}"
        )

    return response.json()
