"""Refresh the Snowflake GIT REPOSITORY that serves ``handler/`` from the default connection."""

from __future__ import annotations

from snowflake.snowpark import Session

REPOSITORY = "PINKY_EXAMPLE.CORE.EXAMPLE_REPO"

if __name__ == "__main__":
    session = Session.builder.getOrCreate()
    session.sql(f"ALTER GIT REPOSITORY {REPOSITORY} FETCH").collect()
    print(f"fetched {REPOSITORY}")
