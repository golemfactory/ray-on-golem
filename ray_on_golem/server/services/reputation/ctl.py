import asyncio
from aerich import Migrate
from pathlib import Path
import click
from ray_on_golem.server.settings import DEFAULT_DATADIR
from ray_on_golem.server.services.reputation.service import ReputationService



@click.group(help="Reputation subsystem management.", context_settings={"show_default": True})
def ctl():
    ...


@ctl.command(help="Initialize the reputation database.")
@click.option(
    "--datadir",
    type=Path,
    help=f"Ray on Golem's data directory. By default, uses a system data directory: {DEFAULT_DATADIR}",
)
def init_db(datadir):
    service = ReputationService(datadir)

    async def init():
        await service.migrations.init_db(True)
        await service.stop()

    asyncio.run(init())


@ctl.command(help="Generate a new migration file.")
@click.option(
    "--datadir",
    type=Path,
    help=f"Ray on Golem's data directory. By default, uses a system data directory: {DEFAULT_DATADIR}",
)
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
        async with ReputationService(datadir) as service:
            await service.migrations.init()
            if empty:
                await Migrate._generate_diff_py(*([name] if name else []))  # noqa
            else:
                await service.migrations.migrate(*([name] if name else []))

    asyncio.run(_migrate())

@ctl.command(help="Show the DB migration files.")
@click.option(
    "--datadir",
    type=Path,
    help=f"Ray on Golem's data directory. By default, uses a system data directory: {DEFAULT_DATADIR}",
)
@click.option(
    "-f",
    "--show-full",
    is_flag=True,
    help="If set, just generate an empty migrations file",
)
def updates(datadir, show_full):
    async def _updates():
        async with ReputationService(datadir) as service:
            db_version = await Migrate.get_last_version()
            if not db_version:
                print("DB uninitialized.")
                return

            print("Current DB version: ", db_version.version)

            updates_available = await service.updates_available()
            if updates_available:
                print("Available updates: ", updates_available)
            else:
                print("The DB seems to be up to date :)")
            if show_full:
                print("Full migration history: ", await service.migrations.history())

    asyncio.run(_updates())


@ctl.command(help="Run all the updates.")
@click.option(
    "--datadir",
    type=Path,
    help=f"Ray on Golem's data directory. By default, uses a system data directory: {DEFAULT_DATADIR}",
)
def upgrade(datadir):
    async def _upgrade():
        async with ReputationService(datadir, autoupdate=False) as service:
            await service.update()

    asyncio.run(_upgrade())
