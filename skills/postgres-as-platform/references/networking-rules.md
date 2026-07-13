# networking-rules

## Table of Contents
1. [The one rule](#the-one-rule)
2. [Address table](#address-table)
3. [Why this bites](#why-this-bites)
4. [Checklist](#checklist)

## The one rule

> **Inside a container, `127.0.0.1` is that container's own loopback — never the host's, never another service's.** Services reach each other by **compose service name**. Host-side tools reach published ports on `127.0.0.1`.

This is the single most-repeated operational rule, inherited from lerdrail. Getting it wrong manifests as "connection refused" the moment code runs inside compose but works on the host.

## Address table

| Perspective | Postgres address |
|---|---|
| The agent app (inside the `agent` container, on the compose network) | **`postgres:5432`** — the service name + port |
| Host-side tools (`psql`, GUI clients, `pgcli`) | **`127.0.0.1:5432`** — the published port (dev compose only) |

So:
- `config.DB_DSN` (read by code running **inside** the container) → `postgresql://USER:PASS@postgres:5432/DBNAME`.
- `.env.example` documents that host tools use `127.0.0.1:5432` against the same published port.

## Why this bites

A developer runs the app on their host first, hardcodes `127.0.0.1` in `DB_DSN`, it works, they commit it, then it breaks the moment the app moves into the container (because the container's `127.0.0.1` has no Postgres). Fix it once, at the source: **`DB_DSN` always uses the service name.**

## Checklist

- [ ] `DB_DSN` in `.env`/`.env.example` uses `postgres` (service name), never `127.0.0.1`/`localhost`, for the in-container app.
- [ ] Dev compose publishes `5432:5432` so host `psql` works; prod compose does **not** publish it.
- [ ] `entrypoint.sh` waits on the service-name host (`pg_isready -h postgres`), not `localhost`.
- [ ] Any docs showing `psql`/GUI examples use `127.0.0.1` and are labeled "host-side".
