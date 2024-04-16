from fastapi import APIRouter, HTTPException

from src.models.models import SearchResponse, VectorSearchRequest
from src.services.standalone import search_standard_db

router = APIRouter()


@router.post(
    "/search_standard_db",
    response_model=SearchResponse,
    response_description="List of documents matching the query",
)
async def search_vectors(request: VectorSearchRequest):
    """
    This endpoint allows you to perform a semantic search in a standards vector database.
    It takes a query string as input and returns a list of documents that match the query.

    - **query**: The search query string
    - **top_k**: The number of documents to return (default 16)
    """
    try:
        result = await search_standard_db.search(request.query, request.top_k)
        return SearchResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
