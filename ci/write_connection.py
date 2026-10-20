"""Write the default Snowflake connection (~/.snowflake/connections.toml) for a CI job.

Reads its configuration from the environment and never prints a secret:

    AUTH                   keypair | oidc
    SNOWFLAKE_ACCOUNT      account identifier
    SNOWFLAKE_WAREHOUSE    warehouse
    SNOWFLAKE_OIDC_USER    user of the federated OIDC identity           (oidc)
    SNOWFLAKE_PRIVATE_KEY  PEM private key of PINKY_CI_SVC               (keypair)
    ACTIONS_ID_TOKEN_REQUEST_URL / _TOKEN  provided by GitHub Actions    (oidc)

The CLI opens its session with ``Session.builder.getOrCreate()``, which reads this file.
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

KEYPAIR_USER = "PINKY_CI_SVC"
ROLE = "DEPLOYER"
AUDIENCE = "snowflakecomputing.com"


def _q(value: str) -> str:
    """TOML basic string (a JSON string is a valid one)."""
    return json.dumps(value)


def _github_id_token() -> str:
    url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"] + f"&audience={AUDIENCE}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"bearer {os.environ['ACTIONS_ID_TOKEN_REQUEST_TOKEN']}"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - GitHub-provided https URL
        token = json.load(resp)["value"]
    print(f"::add-mask::{token}", flush=True)
    return token


def _write_private(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    path.chmod(0o600)


def main() -> None:
    auth = os.environ["AUTH"]
    home = Path.home() / ".snowflake"
    lines = [
        "[default]",
        f"account = {_q(os.environ['SNOWFLAKE_ACCOUNT'])}",
        f"warehouse = {_q(os.environ['SNOWFLAKE_WAREHOUSE'])}",
    ]
    if auth == "keypair":
        key_file = home / "keys" / "ci_key.p8"
        pem = os.environ["SNOWFLAKE_PRIVATE_KEY"]
        _write_private(key_file, pem if pem.endswith("\n") else pem + "\n")
        lines += [
            f"user = {_q(KEYPAIR_USER)}",
            f"role = {_q(ROLE)}",
            'authenticator = "SNOWFLAKE_JWT"',
            f"private_key_file = {_q(str(key_file))}",
        ]
    elif auth == "oidc":
        lines += [
            f"user = {_q(os.environ['SNOWFLAKE_OIDC_USER'])}",
            f"role = {_q(ROLE)}",
            'authenticator = "WORKLOAD_IDENTITY"',
            'workload_identity_provider = "OIDC"',
            f"token = {_q(_github_id_token())}",
        ]
    else:
        raise SystemExit(f"AUTH must be keypair or oidc, got {auth!r}")
    _write_private(home / "connections.toml", "\n".join(lines) + "\n")
    print(f"connection written: auth={auth}")


if __name__ == "__main__":
    main()
