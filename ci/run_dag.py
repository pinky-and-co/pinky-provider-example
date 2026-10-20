"""Run EXAMPLE_DAG and wait for its 5 tasks to end SUCCEEDED.

The first check happens 15 s after ``EXECUTE TASK``, then every 60 s, for at most 15 minutes. Every
check is timestamped. Exits 0 only if INGEST, CLEAN, AGGREGATE, QUALITY and REPORT all SUCCEEDED.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone

DATABASE = "PINKY_EXAMPLE"
SCHEMA = "CORE"
DAG = "EXAMPLE_DAG"
TASKS = [f"{DAG}${t}" for t in ("INGEST", "CLEAN", "AGGREGATE", "QUALITY", "REPORT")]
FIRST_CHECK_S = 15
INTERVAL_S = 60
TIMEOUT_S = 15 * 60
BAD_STATES = {"FAILED", "CANCELLED", "SKIPPED", "FAILED_AND_AUTO_SUSPENDED"}


def log(msg: str) -> None:
    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] {msg}", flush=True)


def run_states(session, since: str) -> dict[str, tuple[str, str | None]]:
    """State and error of every task of the latest run of the DAG started since ``since``."""
    history = (
        f"TABLE({DATABASE}.INFORMATION_SCHEMA.TASK_HISTORY("
        f"SCHEDULED_TIME_RANGE_START => '{since}'::TIMESTAMP_LTZ, RESULT_LIMIT => 1000))"
    )
    root = session.sql(
        f"SELECT GRAPH_RUN_GROUP_ID FROM {history} "
        f"WHERE NAME = '{DAG}' AND SCHEMA_NAME = '{SCHEMA}' "
        "ORDER BY SCHEDULED_TIME DESC LIMIT 1"
    ).collect()
    if not root:
        return {}
    rows = session.sql(
        f"SELECT NAME, STATE, ERROR_MESSAGE FROM {history} "
        f"WHERE GRAPH_RUN_GROUP_ID = '{root[0][0]}' AND SCHEMA_NAME = '{SCHEMA}'"
    ).collect()
    return {r[0]: (r[1], r[2]) for r in rows}


def main() -> int:
    from snowflake.snowpark import Session

    session = Session.builder.getOrCreate()
    since = session.sql("SELECT DATEADD('minute', -1, CURRENT_TIMESTAMP())").collect()[0][0].isoformat()
    session.sql(f"EXECUTE TASK {DATABASE}.{SCHEMA}.{DAG}").collect()
    log(f"EXECUTE TASK {DATABASE}.{SCHEMA}.{DAG} sent")

    started = time.monotonic()
    time.sleep(FIRST_CHECK_S)
    states: dict[str, tuple[str, str | None]] = {}
    while True:
        states = run_states(session, since)
        summary = {t.split("$")[1]: states.get(t, ("PENDING", None))[0] for t in TASKS}
        log(f"check: {summary}")
        if any(states.get(t, ("", None))[0] in BAD_STATES for t in TASKS):
            break
        if all(states.get(t, ("", None))[0] == "SUCCEEDED" for t in TASKS):
            break
        if time.monotonic() - started + INTERVAL_S > TIMEOUT_S:
            log(f"timeout after {TIMEOUT_S // 60} min")
            break
        time.sleep(INTERVAL_S)

    for name, (state, error) in sorted(states.items()):
        log(f"final {name}: {state}" + (f" ({error})" if error else ""))
    ok = all(states.get(t, ("", None))[0] == "SUCCEEDED" for t in TASKS)
    for t in TASKS:
        if t not in states:
            log(f"final {t}: NOT RUN")
    log("DAG OK" if ok else "DAG FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
