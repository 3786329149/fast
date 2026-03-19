from pydantic import BaseModel


class OperationLogOut(BaseModel):
    id: int
    module: str
    action: str
    path: str
