"""Insert a few sample orders into RAW_ORDERS (idempotent: replaces the content)."""

from snowflake.snowpark import Session


def run(session: Session, args: dict) -> dict:
    session.sql("TRUNCATE TABLE PINKY_EXAMPLE.CORE.RAW_ORDERS").collect()
    session.sql(
        """
        INSERT INTO PINKY_EXAMPLE.CORE.RAW_ORDERS
        SELECT * FROM VALUES
          (1, '2026-01-01'::DATE, 'ACME', ' completed ', 3, 10.0),
          (2, '2026-01-01'::DATE, 'GLOBEX', 'Pending', 1, 99.5),
          (3, '2026-01-02'::DATE, 'ACME', 'COMPLETED', 2, 25.0),
          (4, '2026-01-03'::DATE, 'INITECH', 'cancelled', 5, 4.0)
        """
    ).collect()
    return {"continue": 1, "rows": 4}
