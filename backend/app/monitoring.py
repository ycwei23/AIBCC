import logging
import time
from collections import defaultdict

from fastapi import Request

logger = logging.getLogger("aibcc")


class PipelineMetrics:
    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.by_status: dict[str, int] = defaultdict(int)

    def record_status(self, status: str) -> None:
        self.by_status[status] += 1
        if status == "completed":
            self.success_count += 1
        elif status == "failed":
            self.failure_count += 1

    def snapshot(self) -> dict:
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "by_status": dict(self.by_status),
        }


pipeline_metrics = PipelineMetrics()


async def log_request_middleware(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start) * 1000
    logger.info(
        "request method=%s path=%s status=%d duration_ms=%.1f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response
