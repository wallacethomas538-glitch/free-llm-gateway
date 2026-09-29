from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from config import (
    ADMIN_API_KEY,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    PROVIDER_KEYS,
)
from providers import available_providers, chat_completion


app = FastAPI(
    title="VektorFlow Free LLM Gateway",
    version="1.0.0",
    description="Clean OpenAI-compatible multi-provider LLM gateway.",
)


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[dict[str, Any]] = Field(default_factory=list)
    provider: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False


@app.get("/")
async def root():
    return {
        "name": "VektorFlow Free LLM Gateway",
        "version": "1.0.0",
        "status": "online",
        "api": "/v1/chat/completions",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "vektorflow-free-llm-gateway",
        "providers": available_providers(),
    }


@app.get("/v1/models")
async def models():
    models = []

    if PROVIDER_KEYS.get("openrouter"):
        models.append(
            {
                "id": "openrouter",
                "object": "model",
                "owned_by": "openrouter",
            }
        )

    if PROVIDER_KEYS.get("openai"):
        models.append(
            {
                "id": "openai",
                "object": "model",
                "owned_by": "openai",
            }
        )

    if PROVIDER_KEYS.get("groq"):
        models.append(
            {
                "id": "groq",
                "object": "model",
                "owned_by": "groq",
            }
        )

    if PROVIDER_KEYS.get("huggingface"):
        models.append(
            {
                "id": "huggingface",
                "object": "model",
                "owned_by": "huggingface",
            }
        )

    return {
        "object": "list",
        "data": models,
    }


@app.post("/v1/chat/completions")
async def create_chat_completion(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
):

    if ADMIN_API_KEY:
        supplied_key = ""

        if authorization and authorization.lower().startswith("bearer "):
            supplied_key = authorization[7:].strip()

        if supplied_key != ADMIN_API_KEY:
            raise HTTPException(
                status_code=401,
                detail="Invalid gateway API key",
            )

    provider = request.provider or DEFAULT_PROVIDER
    model = request.model or DEFAULT_MODEL

    if not model:
        raise HTTPException(
            status_code=400,
            detail="No model specified. Set DEFAULT_MODEL or provide model.",
        )

    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="Streaming is not enabled in this initial gateway version.",
        )

    kwargs = {}

    if request.temperature is not None:
        kwargs["temperature"] = request.temperature

    if request.max_tokens is not None:
        kwargs["max_tokens"] = request.max_tokens

    try:
        return await chat_completion(
            provider=provider,
            model=model,
            messages=request.messages,
            **kwargs,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )


@app.get("/admin/status")
async def admin_status(
    authorization: str | None = Header(default=None),
):

    if ADMIN_API_KEY:
        supplied_key = ""

        if authorization and authorization.lower().startswith("bearer "):
            supplied_key = authorization[7:].strip()

        if supplied_key != ADMIN_API_KEY:
            raise HTTPException(
                status_code=401,
                detail="Invalid gateway API key",
            )

    return {
        "service": "vektorflow-free-llm-gateway",
        "default_provider": DEFAULT_PROVIDER,
        "default_model": DEFAULT_MODEL,
        "available_providers": available_providers(),
    }
