from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import ADMIN_API_KEY, DEFAULT_MODEL, DEFAULT_PROVIDER, PROVIDER_KEYS
from providers import available_providers, PROVIDERS
from router import chat_with_fallback, stream_with_fallback


app = FastAPI(
    title="VektorFlow Free LLM Gateway",
    version="1.1.0",
    description="Standalone OpenAI-compatible multi-provider gateway for VektorFlow and other clients.",
)


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[dict[str, Any]] = Field(default_factory=list)
    provider: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False


def _authorize(authorization: str | None) -> None:
    if not ADMIN_API_KEY:
        return
    supplied = ""
    if authorization and authorization.lower().startswith("bearer "):
        supplied = authorization[7:].strip()
    if supplied != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid gateway API key")


@app.get("/")
async def root():
    return {
        "name": "VektorFlow Free LLM Gateway",
        "version": "1.1.0",
        "status": "online",
        "api": "/v1/chat/completions",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "vektorflow-free-llm-gateway",
        "configured_providers": available_providers(),
    }


@app.get("/v1/models")
async def models():
    data = []
    for provider, cfg in PROVIDERS.items():
        if PROVIDER_KEYS.get(cfg["key_name"]):
            data.append({"id": provider, "object": "model", "owned_by": provider})
    if DEFAULT_MODEL:
        data.append({"id": DEFAULT_MODEL, "object": "model", "owned_by": "gateway"})
    return {"object": "list", "data": data}


@app.post("/v1/chat/completions")
async def create_chat_completion(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
):
    _authorize(authorization)

    model = request.model or DEFAULT_MODEL
    if not model:
        raise HTTPException(status_code=400, detail="No model specified. Set DEFAULT_MODEL or provide model.")

    kwargs: dict[str, Any] = {}
    if request.temperature is not None:
        kwargs["temperature"] = request.temperature
    if request.max_tokens is not None:
        kwargs["max_tokens"] = request.max_tokens

    try:
        if request.stream:
            route, stream = await stream_with_fallback(
                model=model,
                messages=request.messages,
                preferred_provider=request.provider or DEFAULT_PROVIDER,
                **kwargs,
            )
            return StreamingResponse(
                stream,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-VektorFlow-Provider": route.provider,
                    "X-VektorFlow-Model": route.model,
                },
            )

        return await chat_with_fallback(
            model=model,
            messages=request.messages,
            preferred_provider=request.provider or DEFAULT_PROVIDER,
            **kwargs,
        )

    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/admin/status")
async def admin_status(authorization: str | None = Header(default=None)):
    _authorize(authorization)
    return {
        "service": "vektorflow-free-llm-gateway",
        "default_provider": DEFAULT_PROVIDER,
        "default_model": DEFAULT_MODEL,
        "available_providers": available_providers(),
    }
