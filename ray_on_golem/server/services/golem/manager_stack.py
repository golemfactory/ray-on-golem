import logging
from typing import Dict, Optional

from golem.managers import (
    ActivityManager,
    AgreementManager,
    DemandManager,
    ProposalManager,
    ProposalManagerPlugin,
    ProposalScorer,
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ManagerStack(BaseModel):
    demand_manager: Optional[DemandManager]
    proposal_manager: Optional[ProposalManager]
    agreement_manager: Optional[AgreementManager]
    activity_manager: Optional[ActivityManager]
    extra_proposal_plugins: Dict[str, ProposalManagerPlugin] = Field(default_factory=dict)
    extra_proposal_scorers: Dict[str, ProposalScorer] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    @property
    def _managers(self):
        return [
            self.demand_manager,
            self.proposal_manager,
            self.agreement_manager,
            self.activity_manager,
        ]

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
