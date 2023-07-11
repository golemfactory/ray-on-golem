from enum import Enum
from ipaddress import IPv4Address
from typing import Dict

from pydantic.main import BaseModel

NodeID = str
ClusterID = str


class NodeState(Enum):
    pending = 'pending'
    running = 'running'
    stopping = 'stopping'


class Node(BaseModel):
    node_id: NodeID
    state: NodeState
    tags: Dict
    internal_ip: IPv4Address
    external_ip: IPv4Address | None
