"""A small bounded in-process job queue, standing in for Celery/RQ + Redis for this lightweight
MVP (see PROGRAM_REQUIREMENTS.md 10.1). Provides the same safety property the doc asks for --
a fixed number of concurrent recon jobs -- without extra infrastructure to run locally.
"""

from __future__ import annotations

import asyncio
import logging

from app.config import get_settings

logger = logging.getLogger("ethicalhawk.background")
settings = get_settings()

_queue: asyncio.Queue[str] | None = None
_workers: list[asyncio.Task] = []


def get_queue() -> asyncio.Queue[str]:
    if _queue is None:
        raise RuntimeError("Background queue not started yet")
    return _queue


async def enqueue_run(run_id: str) -> None:
    await get_queue().put(run_id)


async def _worker(worker_id: int) -> None:
    from app.services.pipeline import execute_run

    queue = get_queue()
    while True:
        run_id = await queue.get()
        try:
            await execute_run(run_id)
        except Exception:  # noqa: BLE001
            logger.exception("Worker %s: run %s raised unexpectedly", worker_id, run_id)
        finally:
            queue.task_done()


def start_workers() -> None:
    global _queue
    _queue = asyncio.Queue()
    for i in range(settings.max_concurrent_jobs):
        _workers.append(asyncio.create_task(_worker(i)))


async def stop_workers() -> None:
    for task in _workers:
        task.cancel()
    for task in _workers:
        try:
            await task
        except asyncio.CancelledError:
            pass
    _workers.clear()
