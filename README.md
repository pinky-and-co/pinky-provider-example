# pinky-provider-example

Reference project deployed with [pinky-provider](https://github.com/pinky-and-co/pinky-provider).

| Path | Content |
|---|---|
| `account/` | Account-scope manifest: the `PINKY_EXAMPLE` database. |
| `schema/` | Schema-scope manifest for `PINKY_EXAMPLE.CORE`: 3 tables, 5 procedures, 3 views, 2 functions and one `dag:` of 5 tasks. |
| `handler/` | Python code of the procedures and functions, loaded from a Snowflake GIT REPOSITORY on this repo. |

## The DAG

`EXAMPLE_DAG` (on demand): `INGEST` -> `CLEAN` -> (`AGGREGATE`, `QUALITY`) -> `REPORT`; `REPORT` waits for both branches.
Each task calls one stored procedure taking one `VARIANT` argument and returning a `VARIANT`.

## Deploy

Prerequisites: a Git API integration allowing this repo's GitHub org, and `handler/` pushed to
`main` — Snowflake reads the code from GitHub (`handler_path` in `schema/vars/SANDBOX.yml`), not
from your disk.

1. Apply the account manifest (creates the database):

   ```bash
   pinky-provider apply --env SANDBOX --source account/manifest.yml
   ```

2. Create, once, the schema and the Git repository object that serves `handler/`
   (`artifact_source` fetches it before the schema manifest is applied):

   ```sql
   CREATE SCHEMA IF NOT EXISTS PINKY_EXAMPLE.CORE;
   CREATE GIT REPOSITORY PINKY_EXAMPLE.CORE.EXAMPLE_REPO
     API_INTEGRATION = <your git api integration>
     ORIGIN = 'https://github.com/pinky-and-co/pinky-provider-example.git';
   ```

3. Install the DAG wrapper procedures in the schema, then apply the schema manifest:

   ```bash
   pinky-provider install-wrappers --schema PINKY_EXAMPLE.CORE
   pinky-provider plan  --env SANDBOX --source schema/manifest.yml
   pinky-provider apply --env SANDBOX --source schema/manifest.yml
   ```

4. Run the DAG: `EXECUTE TASK PINKY_EXAMPLE.CORE.EXAMPLE_DAG;`

## CI

`.github/workflows/deploy.yml` deploys this project with GitHub Actions, in `SANDBOX`:

- on a pull request, job `plan` (matrix `auth: [keypair, oidc]`) runs `pinky-provider plan` on the account then the schema manifest; exit code 2 (changes detected) is accepted;
- on a push to `main`, job `apply` (OIDC only) fetches the Git repository, installs the wrappers, applies the account then the schema manifest, then runs `EXAMPLE_DAG` and fails unless its 5 tasks end `SUCCEEDED` (`ci/run_dag.py`: first check after 15 s, then every 60 s, 15 min timeout).

Both jobs run in the GitHub **environment `sandbox`** (Settings > Environments). Its name is part of the OIDC subject.

Each Snowflake step first runs `ci/write_connection.py`, which writes `~/.snowflake/connections.toml` (mode 600) from the settings below; the CLI reads it as the default connection. Secrets are passed through the environment and never printed; the GitHub ID token is masked.

| Kind | Name | Used for |
|---|---|---|
| Variable | `SNOWFLAKE_ACCOUNT` | Account identifier. |
| Variable | `SNOWFLAKE_WAREHOUSE` | Session warehouse. |
| Variable | `SNOWFLAKE_OIDC_USER` | Snowflake user federated with the GitHub OIDC identity (`oidc`). |
| Secret | `SNOWFLAKE_PRIVATE_KEY` | Unencrypted PKCS8 PEM private key of `PINKY_CI_SVC` (`keypair`). |

The key-pair user is `PINKY_CI_SVC` (role `DEPLOYER`). The OIDC user is created once, by hand (the Core API cannot declare a workload identity), next to the Git repository object. The subject is `repo:pinky-and-co/pinky-provider-example:environment:sandbox`:

```sql
CREATE USER <oidc user> TYPE = SERVICE
  WORKLOAD_IDENTITY = (
    TYPE = OIDC
    ISSUER = 'https://token.actions.githubusercontent.com'
    SUBJECT = 'repo:pinky-and-co/pinky-provider-example:environment:sandbox'
  )
  DEFAULT_ROLE = DEPLOYER;
GRANT ROLE DEPLOYER TO USER <oidc user>;
```

Set `SNOWFLAKE_OIDC_USER` to `<oidc user>`. The workflow installs `pinky-provider` from `main` until the release is published.
