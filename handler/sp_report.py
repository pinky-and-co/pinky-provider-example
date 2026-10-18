"""Final step: return the revenue summary."""

from snowflake.snowpark import Session


def run(session: Session, args: dict) -> dict:
    row = session.sql(
        "SELECT COUNT(*), COALESCE(SUM(REVENUE), 0) FROM PINKY_EXAMPLE.CORE.DAILY_SALES"
    ).collect()[0]
    return {"continue": 1, "days": row[0], "revenue": row[1]}
