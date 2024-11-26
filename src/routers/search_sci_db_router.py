from fastapi import APIRouter, HTTPException

from src.models.models import SearchRequest, SearchResponse
from src.services.standalone import search_sci_db

router = APIRouter()


@router.post(
    "/search_sci_db",
    response_model=SearchResponse,
    response_description="List of documents matching the query",
)
async def search_sci(request: SearchRequest):
    """
    This endpoint allows you to perform hybrid search (semantic and key word search) on the academic journal paper database for precise and specialized information.
    It takes a query string as input and returns a list of documents that match the query.

    - **query**: The search query string
    - **top_k**: The number of top chunk results to return (default 8)
    - **ext_k**: The number of additional chunks to include before and after each topK result (default 0)
    """
    try:
        result = await search_sci_db(
            query=request.query,
            top_k=request.top_k,
            ext_k=request.ext_k,
        )
        return SearchResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))