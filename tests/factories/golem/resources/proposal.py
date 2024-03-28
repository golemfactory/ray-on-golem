from datetime import datetime, timezone
from functools import partial
from typing import Dict, Optional, Sequence, Type, Union

import factory
import pytest
from golem.resources import Demand, Proposal, ProposalData

from tests.factories.golem.resources.base import ResourceFactory
from tests.factories.golem.resources.demand import DemandFactory
from tests.factories.golem.resources.payload import ConstraintsFactory, PropertiesFactory


class ProposalDataFactory(factory.Factory):
    class Meta:
        model = ProposalData

    properties = factory.SubFactory(PropertiesFactory)
    constraints = factory.SubFactory(ConstraintsFactory)
    proposal_id = factory.Faker("pystr")
    issuer_id = factory.Faker("pystr")
    state = "Initial"
    timestamp = factory.LazyFunction(partial(datetime.now, timezone.utc))
    prev_proposal_id = None


class ProposalFactory(ResourceFactory):
    class Meta:
        model = Proposal

    data = factory.SubFactory(ProposalDataFactory)

    @factory.post_generation
    def initial(obj: Proposal, _, extracted: bool, **kwargs):  # noqa
        """If specified, ensures the Proposal is treated as `initial`."""

        # force `True` if not defined, iow, produce initial proposals by default
        if extracted is None:
            extracted = True

        if extracted or kwargs:
            demand = DemandFactory(**kwargs)
            demand.add_child(obj)

    @factory.post_generation
    def parent(
        obj: Proposal,
        _,
        extracted: Union[Demand, Proposal],
        parent_factory: Optional[Type[Union[DemandFactory, "ProposalFactory"]]] = None,
        **kwargs,
    ):  # noqa
        """Set a parent on the proposal."""
        if extracted:
            extracted.add_child(obj)
        elif not obj.has_parent:
            if not parent_factory:
                parent_factory = ProposalFactory
            parent = parent_factory(**kwargs)
            parent.add_child(obj)

    @factory.post_generation
    def demand(obj: Proposal, _, extracted: Demand, **kwargs):  # noqa
        """Set a demand on the proposal."""
        if extracted:
            obj.demand = extracted
        elif kwargs:
            obj.demand = DemandFactory(**kwargs)


class ProposalGenerator:
    """Generates the required Proposals with specified factory parameters.

    We provide kwargs, not direct Proposal objects to allow passing them as test parameters.
    As initialization of Proposal object requires an asyncio loop to be runnning, we cannot
    do this declaratively.
    """

    def __init__(self, factory_kwargs: Optional[Sequence[Dict]] = None):
        self.proposals = list()
        self.generator = (ProposalFactory(**kwargs) for kwargs in factory_kwargs or (dict(),))

    async def get_proposal(self) -> Proposal:
        proposal = next(self.generator)
        self.proposals.append(proposal)
        return proposal


@pytest.fixture
def proposal_generator(request):
    factory_kwargs: Sequence[Dict] = ({},)
    try:
        factory_kwargs = request.param
    except AttributeError:
        pass
    return ProposalGenerator(factory_kwargs).get_proposal
