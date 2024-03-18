import factory
from golem.payload import Constraints, Properties


class PropertiesFactory(factory.Factory):
    class Meta:
        model = Properties


class ConstraintsFactory(factory.Factory):
    class Meta:
        model = Constraints
