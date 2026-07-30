"""
Alembic environment configuration.

Why this file was edited (not left as the default alembic init output):
    Two changes from the template: (1) target_metadata points at our
    Base.metadata instead of None, which is what makes `--autogenerate`
    possible at all; (2) the DB URL comes from our own Settings object
    instead of a hardcoded value in alembic.ini, so migrations always run
    against whatever DATABASE_URL the app itself is configured with —
    one source of truth, not two.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config.settings import settings
from app.database.base import Base
import app.models  # noqa: F401  — import triggers registration of every model

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite can't ALTER TABLE directly (e.g. to add
        # a CHECK constraint); batch mode has Alembic recreate the table under
        # the hood instead. No-op on other dialects, so this stays safe if
        # DATABASE_URL is later pointed at MySQL.
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
