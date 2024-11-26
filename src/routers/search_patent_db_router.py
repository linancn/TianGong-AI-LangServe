from fastapi import APIRouter, HTTPException

from src.models.models import SearchRequest, SearchResponse
from src.services.standalone import search_patent_db

router = APIRouter()


@router.post(
    "/search_patent_db",
    response_model=SearchResponse,
    response_description="List of patents matching the query",
)
async def search_patent(request: SearchRequest):
    """
    This endpoint allows you to perform hybrid search (semantic and key word search) on the patent database for precise and specialized information.
    It takes a query string as input and returns a list of documents that match the query.

    - **query**: The search query string
    - **top_k**: The number of top chunk results to return (default 8)
    """
    try:
        result = await search_patent_db.search(
            query=request.query,
            top_k=request.top_k,
        )
        return SearchResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
