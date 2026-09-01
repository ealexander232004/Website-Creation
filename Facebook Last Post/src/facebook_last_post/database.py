"""PostgreSQL queue and result persistence for large lead warehouses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from importlib.resources import files
from typing import Any

import psycopg
from psycopg import Connection, sql
from psycopg.rows import dict_row

from .models import FetchResult, FetchStatus, ProfileJob
from .normalization import InvalidFacebookProfile, normalize_facebook_profile


@dataclass(frozen=True, slots=True)
class EnqueueSummary:
    source_rows: int
    accepted: int
    invalid: int


@dataclass(frozen=True, slots=True)
class PersistenceDecision:
    state: str
    next_attempt_at: datetime | None


def decide_persistence(
    result: FetchResult,
    *,
    attempt_count: int,
    max_attempts: int,
) -> PersistenceDecision:
    if result.status is FetchStatus.OK:
        return PersistenceDecision("succeeded", None)
    if result.status is FetchStatus.NO_POST_TIMESTAMP:
        return PersistenceDecision("no_data", None)
    if result.status in {FetchStatus.NOT_FOUND, FetchStatus.UNAVAILABLE}:
        return PersistenceDecision("unavailable", None)
    if result.status.is_access_control:
        return PersistenceDecision("blocked", None)
    if result.status is FetchStatus.DOCUMENT_TOO_LARGE:
        return PersistenceDecision("failed", None)
    if attempt_count >= max_attempts:
        return PersistenceDecision("failed", None)
    backoff_minutes = min(24 * 60, 5 * (2**attempt_count))
    return PersistenceDecision("retry", result.checked_at + timedelta(minutes=backoff_minutes))


class FacebookActivityStore:
    """Small-transaction repository; external requests never run under DB locks."""

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    def connect(self) -> Connection[Any]:
        return psycopg.connect(self._conninfo, autocommit=True, row_factory=dict_row)

    def migrate(self) -> None:
        migration = (
            files("facebook_last_post.migrations")
            .joinpath("001_facebook_activity.sql")
            .read_text(encoding="utf-8")
        )
        with self.connect() as connection, connection.transaction():
            connection.execute(migration)

    def enqueue_from_socials(
        self,
        *,
        source_schema: str = "warehouse",
        source_table: str = "entity_socials",
        batch_size: int = 2_000,
        limit: int | None = None,
    ) -> EnqueueSummary:
        if batch_size < 1 or batch_size > 10_000:
            raise ValueError("batch_size must be between 1 and 10000")
        if limit is not None and limit < 0:
            raise ValueError("limit cannot be negative")

        relation = sql.Identifier(source_schema, source_table)
        select_query = sql.SQL(
            """
            select entity_id, handle_or_url, source
            from {relation}
            where platform = 'facebook'
              and (entity_id, handle_or_url, source) > (%s, %s, %s)
            order by entity_id, handle_or_url, source
            limit %s
            """
        ).format(relation=relation)
        insert_query = """
            insert into facebook_enrichment.profile_activity (
                entity_id, source, input_handle_or_url, normalized_url
            ) values (%s, %s, %s, %s)
            on conflict (entity_id, source, normalized_url) do update
            set input_handle_or_url = excluded.input_handle_or_url,
                updated_at = current_timestamp
        """

        cursor_key: tuple[int, str, str] = (0, "", "")
        source_rows = accepted = invalid = 0
        with self.connect() as connection:
            while limit is None or source_rows < limit:
                page_size = min(batch_size, limit - source_rows) if limit is not None else batch_size
                rows = connection.execute(select_query, (*cursor_key, page_size)).fetchall()
                if not rows:
                    break

                values: list[tuple[int, str, str, str]] = []
                for row in rows:
                    source_rows += 1
                    try:
                        normalized = normalize_facebook_profile(row["handle_or_url"])
                    except InvalidFacebookProfile:
                        invalid += 1
                        continue
                    values.append(
                        (
                            row["entity_id"],
                            row["source"],
                            row["handle_or_url"],
                            normalized.normalized_url,
                        )
                    )

                if values:
                    with connection.transaction(), connection.cursor() as cursor:
                        cursor.executemany(insert_query, values)
                    accepted += len(values)

                last = rows[-1]
                cursor_key = (last["entity_id"], last["handle_or_url"], last["source"])

        return EnqueueSummary(source_rows, accepted, invalid)

    @staticmethod
    def claim_job(
        connection: Connection[Any],
        *,
        worker_id: str,
        lease_seconds: int,
        max_attempts: int,
    ) -> ProfileJob | None:
        row = connection.execute(
            """
            with candidate as (
                select profile_id
                from facebook_enrichment.profile_activity
                where (
                    (state in ('pending', 'retry') and next_attempt_at <= current_timestamp)
                    or (state = 'leased' and lease_expires_at <= current_timestamp)
                )
                  and attempt_count < %s
                order by coalesce(next_attempt_at, lease_expires_at), profile_id
                for update skip locked
                limit 1
            )
            update facebook_enrichment.profile_activity as activity
            set state = 'leased',
                lease_owner = %s,
                lease_expires_at = current_timestamp + (%s * interval '1 second'),
                attempt_count = activity.attempt_count + 1,
                updated_at = current_timestamp
            from candidate
            where activity.profile_id = candidate.profile_id
            returning activity.profile_id, activity.entity_id, activity.source,
                      activity.input_handle_or_url, activity.normalized_url,
                      activity.attempt_count
            """,
            (max_attempts, worker_id, lease_seconds),
        ).fetchone()
        if row is None:
            return None
        return ProfileJob(**row)

    @staticmethod
    def record_result(
        connection: Connection[Any],
        *,
        worker_id: str,
        job: ProfileJob,
        result: FetchResult,
        max_attempts: int,
    ) -> str:
        decision = decide_persistence(
            result,
            attempt_count=job.attempt_count,
            max_attempts=max_attempts,
        )
        cursor = connection.execute(
            """
            update facebook_enrichment.profile_activity
            set state = %s,
                fetch_status = %s,
                last_post_at = coalesce(%s, last_post_at),
                checked_at = %s,
                next_attempt_at = %s,
                last_http_status = %s,
                extraction_method = %s,
                document_bytes = %s,
                duration_ms = %s,
                error_code = %s,
                error_detail = %s,
                proxy_label = %s,
                lease_owner = null,
                lease_expires_at = null,
                updated_at = current_timestamp
            where profile_id = %s
              and state = 'leased'
              and lease_owner = %s
            """,
            (
                decision.state,
                result.status.value,
                result.last_post_at,
                result.checked_at,
                decision.next_attempt_at,
                result.http_status,
                result.extraction_method,
                result.document_bytes,
                result.duration_ms,
                result.error_code,
                result.error_detail,
                result.proxy_label,
                job.profile_id,
                worker_id,
            ),
        )
        if cursor.rowcount != 1:
            raise RuntimeError(f"lease lost before profile {job.profile_id} could be updated")
        return decision.state

    @staticmethod
    def release_worker_leases(connection: Connection[Any], *, worker_id: str) -> int:
        cursor = connection.execute(
            """
            update facebook_enrichment.profile_activity
            set state = 'retry',
                next_attempt_at = current_timestamp,
                lease_owner = null,
                lease_expires_at = null,
                updated_at = current_timestamp
            where state = 'leased' and lease_owner = %s
            """,
            (worker_id,),
        )
        return cursor.rowcount

    def stats(self) -> dict[str, int]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                select state, count(*)::bigint as count
                from facebook_enrichment.profile_activity
                group by state
                order by state
                """
            ).fetchall()
        return {row["state"]: row["count"] for row in rows}
