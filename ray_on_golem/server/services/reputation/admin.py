import asyncio

import click
from aerich import Migrate

from ray_on_golem.cli import with_datadir
from ray_on_golem.server.services.reputation.service import ReputationService


@click.group(help="Reputation subsystem admin.", context_settings={"show_default": True})
def admin():
    ...


@admin.command(help="Generate a new migration file.")
@with_datadir
@click.option(
    "--name",
    type=str,
    help="The name of the generated migration file",
)
@click.option(
    "--empty",
    is_flag=True,
    help="If set, just generate an empty migrations file",
)
def migrate(datadir, name, empty):
    if empty and not name:
        print("Name is required for an empty migration.")
        return

    async def _migrate():
        migration_name = None
        async with ReputationService(datadir, auto_apply_migrations=False) as service:
            await service.migrations.init()
            if empty:
                migration_name = await Migrate._generate_diff_py(*([name] if name else []))  # noqa
            else:
                migration_name = await service.migrations.migrate(*([name] if name else []))

        if migration_name:
            print("Created a migration: ", migration_name)

    asyncio.run(_migrate())


@admin.command(help="Show the DB migration files.")
@with_datadir
@click.option(
    "-f",
    "--show-full",
    is_flag=True,
    help="If set, just generate an empty migrations file",
)
def updates(datadir, show_full):
    async def _updates():
        async with ReputationService(datadir, auto_apply_migrations=False) as service:
            db_version = await Migrate.get_last_version()
            if not db_version:
                print("DB uninitialized.")
                return

            print("Current DB version: ", db_version.version)

            migrations_available = await service.migrations_available()
            if migrations_available:
                print("Available updates: ", migrations_available)
            else:
                print("The DB seems to be up to date :)")
            if show_full:
                print("Full migration history: ", await service.migrations.history())

    asyncio.run(_updates())


@admin.command(help="Run all the updates.")
@with_datadir
def upgrade(datadir):
    async def _upgrade():
        async with ReputationService(datadir, auto_apply_migrations=False) as service:
            await service.apply_migrations()

    asyncio.run(_upgrade())
