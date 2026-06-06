import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so Alembic can detect them for autogenerate
from app.db.base import Base
from app.models import brand  # noqa
from app.models import user  # noqa
from app.models import brand_config  # noqa
from app.models import tone_setting  # noqa
from app.models import brand_image_style  # noqa
from app.models import moderation_config  # noqa
from app.models import product  # noqa
from app.models import faq  # noqa
from app.models import routine  # noqa
from app.models import compliance_rule  # noqa
from app.models import recommendation_rule  # noqa
from app.models import conversation  # noqa
from app.models import lead  # noqa
from app.models import secret  # noqa
from app.models import prompt_version  # noqa
from app.models import embedding  # noqa
from app.models import logs  # noqa
from app.models import bot_protection  # noqa
from app.models import notification  # noqa
from app.models import widget_event  # noqa

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
