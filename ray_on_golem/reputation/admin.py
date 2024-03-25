import asyncio

import click
from aerich import DowngradeError, Migrate

from ray_on_golem.cli import with_datadir
from ray_on_golem.reputation.service import ReputationService


def _format_migrations(migrations):
    return [f"    {m}\n" for m in migrations]


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

            print("Current DB version: ", db_version.version, "\n")

            migrations_available = await service.migrations_available()
            if migrations_available:
                print("Available updates: \n", *_format_migrations(migrations_available))
            else:
                print("The DB seems to be up to date :)")
            if show_full:
                print(
                    "Full migration history: \n",
                    *_format_migrations(await service.migrations.history()),
                )

    asyncio.run(_updates())


@admin.command(help="Run all the updates.")
@with_datadir
def upgrade(datadir):
    async def _upgrade():
        async with ReputationService(datadir, auto_apply_migrations=False) as service:
            applied_migrations = await service.apply_migrations()
            if applied_migrations:
                print("Applied migrations: \n", *_format_migrations(applied_migrations))
            else:
                print("No new migrations found.")

    asyncio.run(_upgrade())


@admin.command(help="Rollback all the migrations up to and including the given version.")
@with_datadir
@click.argument("version", type=int)
def rollback(datadir, version: int):
    async def _downgrade():
        async with ReputationService(datadir, auto_apply_migrations=False) as service:
            try:
                rolled_back_migrations = await service.downgrade_migrations(version)
                if rolled_back_migrations:
                    print("Rolled-back migrations: \n", *_format_migrations(rolled_back_migrations))
            except DowngradeError:
                print("Migration not found in the DB.")

    asyncio.run(_downgrade())
