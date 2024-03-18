from datetime import datetime, timezone
from functools import partial
from typing import Optional, Type, Union

import factory
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
