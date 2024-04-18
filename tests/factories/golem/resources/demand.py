from golem.resources import Demand

from tests.factories.golem.resources.base import ResourceFactory


class DemandFactory(ResourceFactory):
    class Meta:
        model = Demand
