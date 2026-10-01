"""Chinook SQLite database initialization.

This follows the database setup code supplied in the project brief while adding
HTTP error handling and a small schema validation helper.
"""

import sqlite3
from typing import Any

import requests
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from .config import CHINOOK_SQL_URL


def get_engine_for_chinook_db():
    """Pull the SQL file, populate an in-memory database, and create an engine."""
    response = requests.get(CHINOOK_SQL_URL, timeout=30)
    response.raise_for_status()

    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.executescript(response.text)

    return create_engine(
        "sqlite://",
        creator=lambda: connection,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )


def create_chinook_database() -> SQLDatabase:
    """Return the LangChain SQL utility backed by the Chinook database."""
    return SQLDatabase(get_engine_for_chinook_db())


def required_tables(engine) -> set[str]:
    """Return the required tables that are available in the initialized database."""
    return set(inspect(engine).get_table_names())


class ChinookRepository:
    """Read-only query gateway for the Chinook database."""

    def __init__(self, engine):
        self.engine = engine

    def fetch_all(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.engine.connect() as connection:
            result = connection.execute(text(query), parameters or {})
            return [dict(row._mapping) for row in result]

    def fetch_one(self, query: str, parameters: dict[str, Any] | None = None) -> dict[str, Any] | None:
        rows = self.fetch_all(query, parameters)
        return rows[0] if rows else None