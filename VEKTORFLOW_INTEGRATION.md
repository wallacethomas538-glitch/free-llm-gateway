# VektorFlow Integration

This repository is a standalone inference/provider service. It does not replace VektorFlow's agent architecture or EventBus.

## Boundary

VektorFlow remains the orchestrator:

VektorFlow -> agent/tool -> LLM Gateway -> provider

The gateway exposes:

- GET /health
- GET /v1/models
- POST /v1/chat/completions

## Routing

The gateway can try multiple configured providers when the preferred provider fails. Provider credentials remain deployment secrets.

## EventBus

Agent-to-agent coordination stays inside VektorFlow's EventBus. This service is only an inference/provider boundary. Optional workflow systems may consume VektorFlow events separately; they are not embedded into this gateway.

## Render

Deploy this repository as its own web service. Set provider credentials and ADMIN_API_KEY in Render environment variables.

This repository is intentionally independent of the VektorFlow feature branch. No VektorFlow branch is copied or used as its base.
