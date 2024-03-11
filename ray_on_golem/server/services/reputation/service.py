from contextlib import AbstractAsyncContextManager
import logging
from pathlib import Path
from typing import Optional

from aerich import Command
from tortoise import Tortoise
from tortoise.exceptions import OperationalError

from ray_on_golem.server.settings import get_reputation_db_config


logger = logging.getLogger(__name__)


class ReputationService(AbstractAsyncContextManager):
    def __init__(self, datadir: Optional[Path] = None, autoupdate: bool = False):
        db_config = get_reputation_db_config(datadir)
        self._db_config = db_config.get("db")
        self.migrations = Command(**db_config.get("migrations"))
        self._autoupdate = autoupdate

    async def __aenter__(self) -> "ReputationService":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def updates_available(self):
        return await self.migrations.heads()

    async def update(self):
        try:
            updates_available = await self.updates_available()
            if updates_available:
                logger.info(
                    "Reputation DB updates available: %s. Running migrations.",
                    updates_available
                )
        except OperationalError:
            logger.info("The DB had not yet been initialized. Initializing from scratch.")

        updates_performed = await self.migrations.upgrade(True)
        logger.info("Migrations performed: %s.", updates_performed)

    async def start(self):
        await self.migrations.init()
        if self._autoupdate:
            try:
                await self.update()
            except Exception:
                await self.stop()
                raise

    async def stop(self):
        await Tortoise.close_connections()

