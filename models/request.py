from typing import List

from pydantic.main import BaseModel

from models.types import NodeId


class CreateClusterRequest(BaseModel):
    image_hash: str
    num_workers: int = 1


class CreateNodesRequest(BaseModel):
    count: int


class DeleteNodesRequest(BaseModel):
    node_ids: List[NodeId]

class SetNodeTagsRequest(BaseModel):
    tags: dict
