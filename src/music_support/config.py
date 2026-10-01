"""Application configuration."""

from os import getenv


CHINOOK_SQL_URL = (
    "https://raw.githubusercontent.com/lerocha/chinook-database/master/"
    "ChinookDatabase/DataSources/Chinook_Sqlite.sql"
)
OPENAI_MODEL = getenv("OPENAI_MODEL", "gpt-4o-mini")