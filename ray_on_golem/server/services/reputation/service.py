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
    def __init__(self, datadir: Optional[Path] = None, auto_apply_migrations: bool = True):
        db_config = get_reputation_db_config(datadir)
        self._db_config = db_config.get("db")
        self.migrations = Command(**db_config.get("migrations"))
        self._auto_apply_migrations = auto_apply_migrations

    async def __aenter__(self) -> "ReputationService":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def migrations_available(self):
        return await self.migrations.heads()

    async def apply_migrations(self):
        try:
            migrations_available = await self.migrations_available()
            if not migrations_available:
                return
            logger.info(
                "Reputation DB updates available: %s. Running migrations.",
                migrations_available
            )
        except OperationalError:
            logger.info("The DB had not yet been initialized. Initializing from scratch.")

        migrations_performed = await self.migrations.upgrade(True)
        logger.info("Migrations performed: %s.", migrations_performed)

    async def start(self):
        await self.migrations.init()
        if self._auto_apply_migrations:
            try:
                await self.apply_migrations()
            except Exception:
                await self.stop()
                raise

    async def stop(self):
        await Tortoise.close_connections()

