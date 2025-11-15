#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
from typing import Dict, Any, Iterable

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse

app = FastAPI(title="Mock DeepSeek SSE Upstream")


def build_deepseek_chunk(
    _id: str,
    model: str,
    content: str,
    role: str | None,
    finish_reason: str | None,
    usage: Dict[str, int] | None = None,
) -> Dict[str, Any]:
    """
    Build a DeepSeek-style chat.completion.chunk object.
    """
    delta: Dict[str, Any] = {}
    if content is not None:
        delta["content"] = content
    if role is not None:
        delta["role"] = role

    choice: Dict[str, Any] = {
        "index": 0,
        "delta": delta,
        "finish_reason": finish_reason,
        "logprobs": None,
    }

    obj: Dict[str, Any] = {
        "id": _id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "system_fingerprint": "fp_mock_123456",
        "choices": [choice],
    }

    # Only attach usage on final chunk (if provided)
    if usage is not None:
        obj["usage"] = usage

    return obj


def normal_stream(_id: str, model: str) -> Iterable[str]:
    """
    Normal streaming: sends a sequence of DeepSeek-style chunks, then [DONE].
    """
    # Same sentence as your example, tokenized in a sloppy but illustrative way.
    tokens = ["", "Hello", "!", " How", " can", " I", " assist", " you", " today", "?"]

    # First chunk: empty content but with role=assistant
    first_chunk = build_deepseek_chunk(
        _id=_id,
        model=model,
        content=tokens[0],
        role="assistant",
        finish_reason=None,
        usage=None,
    )
    yield f"data: {json.dumps(first_chunk, ensure_ascii=False)}\n\n"
    time.sleep(0.05)

    # Middle chunks
    for t in tokens[1:-1]:
        chunk = build_deepseek_chunk(
            _id=_id,
            model=model,
            content=t,
            role="assistant",
            finish_reason=None,
            usage=None,
        )
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        time.sleep(0.05)

    # Last token chunk (before finish)
    last_token = tokens[-1]
    last_content_chunk = build_deepseek_chunk(
        _id=_id,
        model=model,
        content=last_token,
        role="assistant",
        finish_reason=None,
        usage=None,
    )
    yield f"data: {json.dumps(last_content_chunk, ensure_ascii=False)}\n\n"
    time.sleep(0.05)

    # Final chunk with finish_reason="stop" + usage
    usage = {
        "completion_tokens": len(tokens) - 1,
        "prompt_tokens": 17,
        "total_tokens": 17 + (len(tokens) - 1),
    }
    final_chunk = build_deepseek_chunk(
        _id=_id,
        model=model,
        content="",
        role=None,
        finish_reason="stop",
        usage=usage,
    )
    yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
    time.sleep(0.02)

    # Termination line
    yield "data: [DONE]\n\n"


def stream_with_error(_id: str, model: str) -> Iterable[str]:
    """
    Stream a few chunks, then simulate an upstream mid-stream disconnect
    by raising an exception.
    """
    tokens = ["", "Partial", " response", " before", " error"]

    # First chunk
    first_chunk = build_deepseek_chunk(
        _id=_id,
        model=model,
        content=tokens[0],
        role="assistant",
        finish_reason=None,
        usage=None,
    )
    yield f"data: {json.dumps(first_chunk, ensure_ascii=False)}\n\n"
    time.sleep(0.05)

    # A couple of middle chunks
    for t in tokens[1:3]:
        chunk = build_deepseek_chunk(
            _id=_id,
            model=model,
            content=t,
            role="assistant",
            finish_reason=None,
            usage=None,
        )
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        time.sleep(0.05)

    # Simulate a hard upstream failure (connection drop)
    # In a real server this might be network-level; here we emulate by raising.
    raise RuntimeError("Upstream SSE connection dropped (simulated)")


@app.post("/v1/chat/completions")
async def deepseek_chat_completions(request: Request):
    """
    Mock DeepSeek Chat Completion SSE endpoint.

    Request JSON (simplified):

    {
      "model": "deepseek-chat",
      "messages": [...],
      "stream": true,
      "test_mode": "normal" | "rate_limit" | "stream_error"
    }
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "Invalid JSON request"}},
        )

    model = payload.get("model", "deepseek-chat")
    stream = payload.get("stream", False)
    test_mode = payload.get("test_mode", "normal")

    # For simplicity, we just derive an id from current time
    _id = f"mock-{int(time.time() * 1000)}"

    # Mode: rate_limit → return 429 JSON error (no SSE stream)
    if test_mode == "rate_limit":
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "rate_limit",
                    "message": "Too many requests (mock rate limit)",
                    "type": "rate_limit_error",
                }
            },
        )

    # Only stream mode is supported in this mock
    if not stream:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "message": "This mock only supports stream=true",
                    "type": "invalid_request_error",
                }
            },
        )

    # Choose which generator to use based on test_mode
    if test_mode == "stream_error":
        generator = stream_with_error(_id=_id, model=model)
    else:
        # default or "normal"
        generator = normal_stream(_id=_id, model=model)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
    )


@app.get("/")
async def root():
    return {"message": "Mock DeepSeek SSE upstream is running"}

