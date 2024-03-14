"""Reputation system DB models."""
from datetime import datetime, timezone

from tortoise import Model, fields
from tortoise.queryset import ExistsQuery, QuerySet
from typing_extensions import Self

BLACKLISTED_NEVER = datetime.fromtimestamp(0, tz=timezone.utc)
BLACKLISTED_FOREVER = datetime.fromtimestamp(2**32, tz=timezone.utc)


class Node(Model):
    """Single Golem node record."""

    id = fields.IntField(pk=True)
    node_id = fields.CharField(max_length=42, unique=True)
    name = fields.TextField(null=True)

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.pk}, {self.node_id}({self.name})>"


class NodeReputation(Model):
    """Reputation scores for Golem nodes."""

    node = fields.ForeignKeyField("models.Node")
    network = fields.ForeignKeyField("models.Network")
    success_rate = fields.FloatField(null=True)
    uptime = fields.FloatField(null=True)
    blacklisted_until = fields.DatetimeField(default=BLACKLISTED_NEVER)

    class Meta:
        unique_together = (("node", "network"),)

    def is_blacklisted(self):
        """Return `True` if the node is currently blacklisted, `False` otherwise."""
        return self.blacklisted_until >= datetime.now(timezone.utc)

    @classmethod
    def get_blacklisted(cls, blacklisted: bool = True) -> QuerySet[Self]:
        """
        Retrieve the currently blacklisted/not blacklisted nodes.

        :param blacklisted: if `True` (the default), return all the blacklisted nodes,
                            if `False`, return all the non-blacklisted nodes.
        """
        now = datetime.now(timezone.utc)
        qs = cls.all()
        if blacklisted:
            qs = qs.filter(blacklisted_until__gt=now)
        else:
            qs = qs.filter(blacklisted_until__lte=now)

        return qs

    @classmethod
    def check_blacklisted(cls, node_id: str, network_name: str) -> ExistsQuery:
        """Run a query to check if the given node is currently blacklisted."""
        return (
            cls.get_blacklisted()
            .filter(node__node_id=node_id, network__network_name=network_name)
            .exists()
        )


class Network(Model):
    """The network (blockchain) that the nodes operate on."""

    id = fields.IntField(pk=True)
    network_name = fields.CharField(max_length=32, unique=True)

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.pk}, {self.network_name}>"
