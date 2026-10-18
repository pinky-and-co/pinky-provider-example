"""CLEAN_ORDERS to DAILY_SALES."""

from snowflake.snowpark import Session


def run(session: Session, args: dict) -> dict:
    session.sql("TRUNCATE TABLE PINKY_EXAMPLE.CORE.DAILY_SALES").collect()
    session.sql(
        """
        INSERT INTO PINKY_EXAMPLE.CORE.DAILY_SALES
        SELECT ORDER_DATE, COUNT(*), SUM(TOTAL)
        FROM PINKY_EXAMPLE.CORE.CLEAN_ORDERS
        GROUP BY ORDER_DATE
        """
    ).collect()
    return {"continue": 1}
