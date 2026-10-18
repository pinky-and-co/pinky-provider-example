"""Quality check: CLEAN_ORDERS must hold as many rows as RAW_ORDERS."""

from snowflake.snowpark import Session


def run(session: Session, args: dict) -> dict:
    raw = session.table("PINKY_EXAMPLE.CORE.RAW_ORDERS").count()
    clean = session.table("PINKY_EXAMPLE.CORE.CLEAN_ORDERS").count()
    if raw != clean:
        raise ValueError(f"row count mismatch: raw={raw} clean={clean}")
    return {"continue": 1, "rows": clean}
