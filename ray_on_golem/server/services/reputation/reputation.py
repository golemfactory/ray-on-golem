from pathlib import Path
from typing import Optional

from aerich import Command
from tortoise import Tortoise


from ray_on_golem.server.settings import get_reputation_db_config


class Reputation:
    def __init__(self, datadir: Optional[Path] = None):
        db_config = get_reputation_db_config(datadir)
        self._db = Tortoise.init(db_config.get("db"))
        self._migrations = Command(**db_config.get("migrations"))

    async def initialize(self):
        await self._migrations.init()
        await self._migrations.init_db(True)

