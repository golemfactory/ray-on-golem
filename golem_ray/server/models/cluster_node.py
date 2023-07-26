from ipaddress import IPv4Address
from typing import Optional, Dict

from golem_core.core.activity_api.resources import Activity
from pydantic.main import BaseModel

from models.types import NodeState


class ClusterNode(BaseModel):
    node_id: int
    activity: Optional[Activity]
    internal_ip: IPv4Address
    external_ip: Optional[IPv4Address]
    state: Optional[NodeState]
    connection_uri: Optional[str]
    tags: Dict = {}

    class Config:
        arbitrary_types_allowed = True
