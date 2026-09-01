"""Environment-backed configuration without logging credentials."""

from __future__ import annotations

import os
from dataclasses import dataclass

from psycopg.conninfo import make_conninfo


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    conninfo: str

    @classmethod
    def from_environment(cls, *, database: str | None = None) -> "DatabaseConfig":
        explicit = os.getenv("FACEBOOK_DATABASE_URL") or os.getenv("DATABASE_URL")
        if explicit and database is None:
            return cls(explicit)

        dbname = database or os.getenv("FACEBOOK_POSTGRES_DB") or "lead_warehouse"
        parameters: dict[str, str | int] = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "user": os.getenv("POSTGRES_USER", "gmaps_scraper"),
            "password": os.getenv("POSTGRES_PASSWORD", "gmaps_scraper"),
            "dbname": dbname,
            "connect_timeout": 10,
            "application_name": "facebook_last_post",
        }
        sslmode = os.getenv("POSTGRES_SSLMODE")
        if sslmode:
            parameters["sslmode"] = sslmode
        return cls(make_conninfo(**parameters))
