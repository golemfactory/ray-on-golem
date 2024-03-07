from tortoise import fields, Model


class Node(Model):
    """Single Golem node record."""

    id = fields.IntField(pk=True)
    node_id = fields.CharField(max_length=42, unique=True)
    name = fields.TextField()


class NodeReputation(Model):
    """Reputation scores for Golem nodes."""

    node_id = fields.ForeignKeyField("models.Node")
    success_rate = fields.FloatField()
    uptime = fields.FloatField()

