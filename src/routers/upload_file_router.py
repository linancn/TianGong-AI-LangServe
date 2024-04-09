from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.models.models import UploadFileResponse
from src.services.standalone.upload_file import handle_file_upload

router = APIRouter()


@router.post(
    "/upload_file",
    response_model=UploadFileResponse,
    description="Upload a file to the server.",
)
async def upload_file(file: UploadFile = File(...), session_id: str = Form(...)):
    """
    Upload a file to the server.
    """
    try:
        response = await handle_file_upload(file=file, session_id=session_id)
        return UploadFileResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
