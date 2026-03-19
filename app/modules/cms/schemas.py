from pydantic import BaseModel


class BannerOut(BaseModel):
    id: int
    title: str
    image_url: str


class NoticeOut(BaseModel):
    id: int
    title: str
    content: str
