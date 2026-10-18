"""RAW_ORDERS to CLEAN_ORDERS, using the example UDFs."""

from snowflake.snowpark import Session


def run(session: Session, args: dict) -> dict:
    session.sql("TRUNCATE TABLE PINKY_EXAMPLE.CORE.CLEAN_ORDERS").collect()
    session.sql(
        """
        INSERT INTO PINKY_EXAMPLE.CORE.CLEAN_ORDERS
        SELECT ORDER_ID, ORDER_DATE, CUSTOMER,
               PINKY_EXAMPLE.CORE.NORMALIZE_STATUS(STATUS),
               PINKY_EXAMPLE.CORE.ORDER_TOTAL(QUANTITY, UNIT_PRICE)
        FROM PINKY_EXAMPLE.CORE.RAW_ORDERS
        """
    ).collect()
    return {"continue": 1}
