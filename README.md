# pinky-provider-example

Reference project deployed with [pinky-provider](https://github.com/pinky-and-co/pinky-provider).

| Path | Content |
|---|---|
| `account/` | Account-scope manifest: the `PINKY_EXAMPLE` database. |
| `schema/` | Schema-scope manifest for `PINKY_EXAMPLE.CORE`: 3 tables, 5 procedures, 3 views, 2 functions and one `dag:` of 5 tasks. |
| `handler/` | Python code of the procedures and functions, loaded from a Snowflake GIT REPOSITORY on this repo. |

## The DAG

`EXAMPLE_DAG` (on demand): `INGEST` -> `CLEAN` -> `AGGREGATE` and `QUALITY` -> `REPORT`.
Each task calls one stored procedure taking one `VARIANT` argument and returning a `VARIANT`.

## Deploy

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
