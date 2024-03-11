from tortoise import fields, Model
from datetime import datetime, timezone

BLACKLISTED_NEVER = datetime.fromtimestamp(0, tz=timezone.utc)
BLACKLISTED_FOREVER = datetime.fromtimestamp(2**32, tz=timezone.utc)


class Node(Model):
    """Single Golem node record."""

    id = fields.IntField(pk=True)
    node_id = fields.CharField(max_length=42, unique=True)
    name = fields.TextField(null=True)


class NodeReputation(Model):
    """Reputation scores for Golem nodes."""

    node = fields.ForeignKeyField("models.Node")
    network = fields.ForeignKeyField("models.Network")
    success_rate = fields.FloatField(null=True)
    uptime = fields.FloatField(null=True)
    blacklisted_until = fields.DatetimeField(default=BLACKLISTED_NEVER)


class Network(Model):
    """The network (blockchain) that the nodes operate on."""

    id = fields.IntField(pk=True)
    network_name = fields.CharField(max_length=32, unique=True)
