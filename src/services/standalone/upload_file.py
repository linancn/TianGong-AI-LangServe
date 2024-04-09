import mimetypes
import uuid

from fastapi import File


async def handle_file_upload(file: File, session_id: str) -> dict:
    file_content = await file.read()
    extension = mimetypes.guess_extension(file.content_type)
    file_path = f"/tmp/{session_id}_{uuid.uuid4()}{extension}"
    with open(file_path, "wb") as f:
        f.write(file_content)
    return {
        "file_path": file_path,
        "session_id": session_id,
        "status": "success",
    }
