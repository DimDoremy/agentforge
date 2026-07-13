# dev vs prod

Two **standalone** compose files (per the design decision), not an override
stack. Each is self-contained and readable in isolation.

| Aspect | `docker-compose.dev.yml` | `docker-compose.prod.yml` |
|---|---|---|
| Goal | fast feedback, live editing | reproducible, restart-safe |
| Agent image target | `dev` (`uv sync --all-extras`) | `prod` (`uv sync --frozen --no-dev`) |
| Source mount | yes (`.:/app`) | no |
| Runtime command | `uv run langgraph dev …` (reload) | `langgraph up …` |
| Postgres published port | `5432:5432` (host tools) | not published (internal) |
| Restart policy | default | `unless-stopped` |
| Volume | `pgdata_dev` | `pgdata_prod` |
| Detached | foreground (interactive) | `-d` |
| Tier-2 extensions | not installed | opt-in via profile/build-arg |

## Run

```bash
# dev (foreground, logs stream, hot reload):
docker compose -f docker-compose.dev.yml up

# prod (detached):
docker compose -f docker-compose.prod.yml up -d
```

## Shared topology

Both bring up exactly two services — `postgres` (Tier-1 extensions via
`docker/postgres.Dockerfile`) and `agent`. The `agent` service runs
`docker/entrypoint.sh`, which:

1. waits for Postgres health (service-name host),
2. applies `extensions.sql`,
3. runs `platform.setup_all()`,
4. hands off to the runtime command.

See [`skills/harness-workflow/references/dev-vs-prod.md`](../skills/harness-workflow/references/dev-vs-prod.md)
for the full field-by-field breakdown.

## Prod prerequisites

Prod compose requires these env vars to be set (it errors out otherwise, unlike dev):
`DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_DSN`, `MODEL`. Put them in a prod `.env`
(or your secret manager). Never reuse dev credentials.
