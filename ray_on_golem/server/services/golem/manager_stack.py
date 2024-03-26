import logging
from typing import TypeVar

from golem.managers import Manager

TManager = TypeVar("TManager", bound=Manager)

logger = logging.getLogger(__name__)


class ManagerStack:
    def __init__(self) -> None:
        self._managers = []

    def add_manager(self, manager: TManager) -> TManager:
        self._managers.append(manager)
        return manager

    async def start(self) -> None:
        logger.info("Starting stack managers...")

        for manager in self._managers:
            if manager is not None:
                await manager.start()

        logger.info("Starting stack managers done")

    async def stop(self) -> None:
        logger.info("Stopping stack managers...")

        for manager in reversed(self._managers):
            if manager is not None:
                try:
                    await manager.stop()
                except Exception:
                    logger.exception(f"{manager} stop failed!")

        logger.info("Stopping stack managers done")
