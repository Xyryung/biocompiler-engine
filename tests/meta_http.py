"""Exercise the installed SDK's real JSON/SSE decoding with an in-process transport."""

import json
from collections import deque

import httpx2
from openai import AsyncOpenAI

from biocompiler.config import Settings
from biocompiler.providers.meta import MetaProvider


class MetaHTTP:
    def __init__(self):
        self.replies = deque()
        self.requests = []

    async def handle(self, request):
        assert request.url.host == "api.meta.ai"
        assert request.headers["authorization"] == "Bearer transport-test-key"
        self.requests.append((request.url.path, json.loads(request.content)))
        if not self.replies:
            raise AssertionError("Unexpected model request")
        reply = self.replies.popleft()
        if isinstance(reply, Exception):
            raise reply
        return reply

    def provider(self):
        settings = Settings(_env_file=None, meta_api_key="transport-test-key")
        client = AsyncOpenAI(
            api_key="transport-test-key",
            base_url=settings.meta_base_url,
            max_retries=0,
            http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(self.handle)),
        )
        return MetaProvider(settings, client=client)


def completion(content, *, refusal=None, finish_reason="stop", choices=True):
    return httpx2.Response(
        200,
        json={
            "id": "chatcmpl_transport_test",
            "object": "chat.completion",
            "created": 0,
            "model": "muse-spark-1.3",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": finish_reason,
                    "message": {"role": "assistant", "content": content, "refusal": refusal},
                }
            ]
            if choices
            else [],
        },
    )


class SSEBody(httpx2.AsyncByteStream):
    def __init__(self, events):
        self.data = "".join("data: " + json.dumps(event) + "\n\n" for event in events).encode()
        self.closed = False

    async def __aiter__(self):
        for offset in range(0, len(self.data), 997):
            yield self.data[offset : offset + 997]

    async def aclose(self):
        self.closed = True


def segmentation(text, *, terminal="completed"):
    response = {
        "id": "resp_transport_test",
        "object": "response",
        "created_at": 0,
        "model": "sam-3.1",
        "output": [],
        "status": "in_progress",
    }
    item = {
        "id": "msg_transport_test",
        "type": "message",
        "role": "assistant",
        "status": "in_progress",
        "content": [],
    }
    events = [
        {"type": "response.created", "response": response.copy()},
        {"type": "response.output_item.added", "output_index": 0, "item": item.copy()},
        {
            "type": "response.content_part.added",
            "item_id": item["id"],
            "output_index": 0,
            "content_index": 0,
            "part": {"type": "output_text", "text": "", "annotations": []},
        },
    ]
    for delta in (text[:47], text[47:503], text[503:]):
        events.append(
            {
                "type": "response.output_text.delta",
                "item_id": item["id"],
                "output_index": 0,
                "content_index": 0,
                "delta": delta,
            }
        )
    part = {"type": "output_text", "text": text, "annotations": []}
    item.update(status="completed", content=[part])
    # Meta emits this finalizer, without a response.output_text.done event.
    events += [
        {
            "type": "response.content_part.done",
            "item_id": item["id"],
            "output_index": 0,
            "content_index": 0,
            "part": part,
        },
        {"type": "response.output_item.done", "output_index": 0, "item": item},
    ]
    if terminal:
        response.update(status=terminal, output=[item])
        if terminal == "incomplete":
            response["incomplete_details"] = {"reason": "max_output_tokens"}
        events.append({"type": f"response.{terminal}", "response": response})
    for number, event in enumerate(events):
        event["sequence_number"] = number
    body = SSEBody(events)
    return httpx2.Response(200, headers={"content-type": "text/event-stream"}, stream=body), body


def sam_plate_text(object_ids=None):
    from biocompiler.vision.synthetic import HEIGHT, WIDTH, center

    records = []
    for object_id in object_ids or range(1, 97):
        row, col = divmod(object_id - 1, 12)
        x, y = center(row, col)
        # Small, lossless test masks in reverse response order.
        records.append(
            f"{object_id}"
            f"<|box;x1={x - 2};y1={y - 2};x2={x + 2};y2={y + 2};w={WIDTH};h={HEIGHT}|>"
            "<|mask;x=0;y=0;data=5,5,!!!!!(QO(0lu8?|>"
        )
    return "<0f>" + ",".join(reversed(records)) + "\n"
