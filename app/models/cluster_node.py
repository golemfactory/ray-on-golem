from ipaddress import IPv4Address

from golem_core.core.activity_api.resources import Activity

from models.types import NodeState


# TODO: change to pydantic
class ClusterNode:
    def __init__(self, node_id: str,
                 internal_ip: IPv4Address,
                 activity: Activity = None,
                 connection_uri: str = None):
        self.node_id = node_id
        self.activity = activity
        self.internal_ip = internal_ip
        self.external_ip = None
        self.state = NodeState.pending
        self.connection_uri = connection_uri
