from fastapi import APIRouter, Depends

from app.api.deps import get_current_client_user
from app.core.response import success
from app.modules.file.schemas import UploadTokenRequest
from app.modules.file.service import service

router = APIRouter(prefix='/files', tags=['File Client'])


@router.post('/upload-token', dependencies=[Depends(get_current_client_user)])
async def create_client_upload_token(payload: UploadTokenRequest) -> dict:
    return success(service.create_upload_token(payload.file_name, payload.content_type))
