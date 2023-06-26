import json
from ipaddress import IPv4Address

from models.types import NodeState


class NodesResponseEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, NodeState):
            return obj.value
        elif isinstance(obj, IPv4Address):
            return str(obj)
        return super().default(obj)
