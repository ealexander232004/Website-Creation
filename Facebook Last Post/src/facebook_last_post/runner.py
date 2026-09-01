"""Concurrent, fixed-route queue runner with access-control circuit breaking."""

from __future__ import annotations

import logging
import socket
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .database import FacebookActivityStore
from .extractor import FacebookPublicDocumentClient
from .models import FetchStatus, RunSummary


logger = logging.getLogger("facebook_last_post.runner")


@dataclass(slots=True)
class _Budget:
    maximum: int | None
    reserved: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def reserve(self) -> bool:
        with self.lock:
            if self.maximum is not None and self.reserved >= self.maximum:
                return False
            self.reserved += 1
            return True

    def release(self) -> None:
        with self.lock:
            self.reserved = max(0, self.reserved - 1)


@dataclass(slots=True)
class _Totals:
    claimed: int = 0
    succeeded: int = 0
    no_data: int = 0
    unavailable: int = 0
    blocked: int = 0
    retried_or_failed: int = 0
    consecutive_no_data: int = 0
    halted_reason: str | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, state: str) -> int:
        with self.lock:
            self.claimed += 1
            if state == "succeeded":
                self.succeeded += 1
                self.consecutive_no_data = 0
            elif state == "no_data":
                self.no_data += 1
                self.consecutive_no_data += 1
            elif state == "unavailable":
                self.unavailable += 1
                self.consecutive_no_data = 0
            elif state == "blocked":
                self.blocked += 1
            else:
                self.retried_or_failed += 1
            return self.consecutive_no_data

    def halt(self, reason: str) -> None:
        with self.lock:
            if self.halted_reason is None:
                self.halted_reason = reason

    def snapshot(self) -> RunSummary:
        with self.lock:
            return RunSummary(
                claimed=self.claimed,
                succeeded=self.succeeded,
                no_data=self.no_data,
                unavailable=self.unavailable,
                blocked=self.blocked,
                retried_or_failed=self.retried_or_failed,
                halted_reason=self.halted_reason,
            )


def run_queue(
    *,
    store: FacebookActivityStore,
    proxy_url: str,
    route_label: str,
    workers: int = 1,
    max_jobs: int | None = None,
    max_attempts: int = 3,
    max_consecutive_no_data: int = 20,
    timeout_seconds: float = 35.0,
    delay_seconds: float = 5.0,
    max_document_bytes: int = 5_000_000,
) -> RunSummary:
    """Process queued profiles without changing egress routes after a block."""

    if not proxy_url:
        raise ValueError("a proxy URL is required; direct fallback is disabled")
    if workers < 1 or workers > 4:
        raise ValueError("workers must be between 1 and 4")
    if max_jobs is not None and max_jobs < 1:
        raise ValueError("max_jobs must be positive when provided")
    if max_consecutive_no_data < 1:
        raise ValueError("max_consecutive_no_data must be positive")
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if delay_seconds < 0:
        raise ValueError("delay_seconds cannot be negative")
    if max_document_bytes < 1:
        raise ValueError("max_document_bytes must be positive")

    stop = threading.Event()
    budget = _Budget(max_jobs)
    totals = _Totals()
    run_token = uuid.uuid4().hex[:10]
    lease_seconds = max(120, int(timeout_seconds + delay_seconds + 60))

    def worker(worker_number: int) -> None:
        worker_id = f"{socket.gethostname()}:{run_token}:{worker_number}"
        connection = store.connect()
        try:
            with FacebookPublicDocumentClient(
                proxy_url=proxy_url,
                route_name=route_label,
                timeout_seconds=timeout_seconds,
                min_interval_seconds=delay_seconds,
                max_document_bytes=max_document_bytes,
            ) as client:
                while not stop.is_set() and budget.reserve():
                    job = store.claim_job(
                        connection,
                        worker_id=worker_id,
                        lease_seconds=lease_seconds,
                        max_attempts=max_attempts,
                    )
                    if job is None:
                        budget.release()
                        return

                    result = client.fetch(job.normalized_url)
                    state = store.record_result(
                        connection,
                        worker_id=worker_id,
                        job=job,
                        result=result,
                        max_attempts=max_attempts,
                    )
                    consecutive_no_data = totals.record(state)
                    logger.info(
                        "profile_id=%d entity_id=%d fetch_status=%s state=%s "
                        "last_post_at=%s http_status=%s bytes=%d duration_ms=%d route=%s",
                        job.profile_id,
                        job.entity_id,
                        result.status.value,
                        state,
                        result.last_post_at.isoformat() if result.last_post_at else None,
                        result.http_status,
                        result.document_bytes,
                        result.duration_ms,
                        route_label,
                    )

                    if result.status.is_access_control:
                        totals.halt(result.status.value)
                        stop.set()
                        return
                    if result.status in {
                        FetchStatus.NETWORK_ERROR,
                        FetchStatus.HTTP_ERROR,
                        FetchStatus.DOCUMENT_TOO_LARGE,
                        FetchStatus.PARSE_ERROR,
                    }:
                        totals.halt(result.status.value)
                        stop.set()
                        return
                    if consecutive_no_data >= max_consecutive_no_data:
                        totals.halt(f"consecutive_no_data:{consecutive_no_data}")
                        stop.set()
                        return
        except Exception as exc:
            totals.halt(f"worker_error:{type(exc).__name__}")
            stop.set()
            logger.exception("worker %d stopped", worker_number)
        finally:
            try:
                store.release_worker_leases(connection, worker_id=worker_id)
            finally:
                connection.close()

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="facebook-public") as executor:
        futures = [executor.submit(worker, number) for number in range(1, workers + 1)]
        for future in futures:
            future.result()

    return totals.snapshot()
