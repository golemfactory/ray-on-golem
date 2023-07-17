from typing import List, Dict

from pydantic.main import BaseModel

from models.types import NodeID


class CreateClusterRequest(BaseModel):
    image_hash: str
    network: str
    budget: int
    num_workers: int = 1


class CreateNodesRequest(BaseModel):
    count: int
    tags: Dict


class DeleteNodesRequest(BaseModel):
    node_ids: List[NodeID]


class SetNodeTagsRequest(BaseModel):
    tags: Dict
