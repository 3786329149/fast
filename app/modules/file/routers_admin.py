from fastapi import APIRouter

from app.core.response import success
from app.modules.file.schemas import UploadTokenRequest
from app.modules.file.service import service

router = APIRouter(prefix='/files', tags=['File Admin'])


@router.post('/upload-token')
async def create_admin_upload_token(payload: UploadTokenRequest) -> dict:
    return success(service.create_upload_token(payload.file_name, payload.content_type))
