from ipaddress import IPv4Address

from pydantic.main import BaseModel

NODE_ID = str
CLUSTER_ID = str


class Node(BaseModel):
    node_id: NODE_ID
    internal_ip: IPv4Address
    external_ip: IPv4Address
