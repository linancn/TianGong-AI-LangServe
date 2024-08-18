from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"}, status_code=status.HTTP_200_OK)
