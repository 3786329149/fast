from pydantic import BaseModel


class UploadTokenRequest(BaseModel):
    file_name: str
    content_type: str


class UploadTokenResponse(BaseModel):
    provider: str
    upload_url: str
    object_key: str
