from pydantic import BaseModel


class ConfigOut(BaseModel):
    key: str
    value: str


class DictOut(BaseModel):
    type: str
    label: str
    value: str
