"""UDF: trimmed, upper-cased status."""


def run(status: str) -> str:
    return status.strip().upper() if status else status
