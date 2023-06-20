from pydantic.main import BaseModel


class CreateNodesRequest(BaseModel):
    count: int
