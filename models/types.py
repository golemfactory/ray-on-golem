from enum import Enum
from ipaddress import IPv4Address

from pydantic.main import BaseModel

NODE_ID = str
CLUSTER_ID = str


class NodeState(Enum):
    pending = 'pending'
    running = 'running'
    stopping = 'stopping'


class Node(BaseModel):
    node_id: NODE_ID
    state: NodeState
    internal_ip: IPv4Address
    external_ip: IPv4Address | None
