"""Single source of truth for runtime configuration.

All environment access goes through :class:`Settings`. No other module reads
``os.environ`` directly — swap values via ``.env``, never via code edits.

See ``skills/postgres-as-platform/references/networking-rules.md`` for the
container-vs-host DB address rule: ``DB_DSN`` uses the **service name** so that
it resolves inside the compose network; host-side tools use ``127.0.0.1``.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment / ``.env``.

    Provider keys are optional because :func:`agentforge_template.models.get_model`
    routes to the right one based on the ``MODEL`` prefix (``openai:...`` vs
    ``anthropic:...`` vs ...). Set the key(s) you actually use.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- LLM -----------------------------------------------------------------
    # Provider-agnostic model string consumed by langchain's init_chat_model.
    # Examples: "openai:gpt-4o-mini", "anthropic:claude-3-5-sonnet-latest".
    model: str = Field(default="openai:gpt-4o-mini", validation_alias="MODEL")

    # Only the key(s) for the provider(s) you use need to be set.
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # --- Postgres platform ---------------------------------------------------
    # Inside compose this uses the service name `postgres`; see networking-rules.md.
    db_dsn: str = Field(
        default="postgresql://postgres:postgres@postgres:5432/agentforge?sslmode=disable",
        validation_alias="DB_DSN",
    )
    db_name: str = Field(default="agentforge", validation_alias="DB_NAME")

    # --- HTTP ----------------------------------------------------------------
    port: int = Field(default=8000, validation_alias="PORT")
    host: str = Field(default="0.0.0.0", validation_alias="HOST")


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached :class:`Settings`."""
    return Settings()
