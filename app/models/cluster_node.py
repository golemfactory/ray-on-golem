from enum import Enum
from ipaddress import IPv4Address
from typing import Any, Optional

from pydantic.main import BaseModel

from models.response import GetNodeResponse
from models.types import Node, NodeState
from golem_core.core.activity_api.resources import Activity

class ClusterNode(BaseModel):
    node_id: int
    activity: Optional[Activity]
    internal_ip: IPv4Address
    external_ip: Optional[IPv4Address]
    state: Optional[NodeState]
    connection_uri: Optional[str]

    class Config:
        arbitrary_types_allowed = True
