from enum import Enum
from ipaddress import IPv4Address
from typing import Any

from pydantic.main import BaseModel

from models.response import GetNodeResponse
from models.types import Node, NodeState, NODE_ID, CLUSTER_ID
from golem_core.low import Activity


class ClusterNode:
    def __init__(self, node_id: str,
                 internal_ip: IPv4Address,
                 activity: Activity = None):
        self.node_id = node_id
        self.activity = activity
        self.internal_ip = internal_ip
        self.external_ip = None
        self.state = NodeState.pending

    def _convert_to_dict(self, obj: Any) -> Any:
        if isinstance(obj, BaseModel):
            data = obj.dict()
            for field_name, field_value in data.items():
                if isinstance(field_value, Enum):
                    data[field_name] = field_value.value
                elif isinstance(field_value, IPv4Address):
                    data[field_name] = str(field_value)
            return {k: self._convert_to_dict(v) for k, v in data.items()}
        else:
            return obj

    def get_response_dict(self) -> Node:
        """Returns response dict with needed fields"""
        attributes = self._convert_to_dict(self.__dict__)
        # attributes.pop('activity', None)
        attributes['internal_ip'] = str(attributes['internal_ip'])
        if attributes.get('external_ip'):
            attributes['external_ip'] = str(attributes['external_ip'])

        return Node(**{i: attributes[i] for i in attributes if i != 'activity'})
