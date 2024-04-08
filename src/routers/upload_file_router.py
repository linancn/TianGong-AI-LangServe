import os

from fastapi import APIRouter, HTTPException, UploadFile

from src.models.models import FileUploadRequest

router = APIRouter()


@router.post(
    "/upload_file",
    response_model=None,
    description="Upload a file to the server.",
)
async def upload_file(file: UploadFile, request: FileUploadRequest):
    """
    Upload a file to the server.
    """
    try:
        file_contents = await request.file.read()
        with open(os.path.join("/tmp", request.session_id), "wb") as f:
            f.write(file_contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
