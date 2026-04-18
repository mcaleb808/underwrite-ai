"""In-process pub/sub for live task events.

This is intentionally simple: a dict of task_id -> set[Queue]. Each SSE
subscriber gets its own queue so back-pressure is per-client. When the
producer signals completion via `close(task_id)`, every subscriber receives
a sentinel `None` and exits.

For multi-worker / multi-host deployments this can be swapped for a
Redis pub/sub later — the publish/subscribe surface stays identical.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any

_subscribers: dict[str, set[asyncio.Queue[dict[str, Any] | None]]] = defaultdict(set)


def subscribe(task_id: str) -> asyncio.Queue[dict[str, Any] | None]:
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue(maxsize=256)
    _subscribers[task_id].add(queue)
    return queue


def unsubscribe(task_id: str, queue: asyncio.Queue[dict[str, Any] | None]) -> None:
    queues = _subscribers.get(task_id)
    if queues is None:
        return
    queues.discard(queue)
    if not queues:
        _subscribers.pop(task_id, None)


async def publish(task_id: str, event: dict[str, Any]) -> None:
    for q in list(_subscribers.get(task_id, ())):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            # drop event for slow consumers rather than block the producer
            continue


async def close(task_id: str) -> None:
    """Signal completion to every subscriber for this task."""
    for q in list(_subscribers.get(task_id, ())):
        try:
            q.put_nowait(None)
        except asyncio.QueueFull:
            continue


async def stream(task_id: str) -> AsyncIterator[dict[str, Any]]:
    """Yield events for a task until a close sentinel is received."""
    queue = subscribe(task_id)
    try:
        while True:
            event = await queue.get()
            if event is None:
                return
            yield event
    finally:
        unsubscribe(task_id, queue)
