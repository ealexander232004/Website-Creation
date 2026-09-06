"""Regression tests for schema initialization behavior."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from database import Database


class DatabaseInitializationTests(unittest.TestCase):
    def test_schema_initialization_remains_enabled_by_default(self) -> None:
        with patch.object(Database, "_init_schema") as initialize:
            Database("postgresql://example.invalid/database")

        initialize.assert_called_once_with()

    def test_read_only_client_can_skip_schema_initialization(self) -> None:
        with patch.object(Database, "_init_schema") as initialize:
            Database("postgresql://example.invalid/database", initialize_schema=False)

        initialize.assert_not_called()


if __name__ == "__main__":
    unittest.main()
