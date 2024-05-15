from fastapi import APIRouter, HTTPException

from src.models.models import SearchResponse, VectorSearchRequestWithIds
from src.services.standalone import search_esg_db

router = APIRouter()


@router.post(
    "/search_esg_db",
    response_model=SearchResponse,
    response_description="List of documents matching the query",
)
async def search_vectors(request: VectorSearchRequestWithIds):
    """
    This endpoint allows you to perform a semantic search in esg reports vector database.
    It takes a query string as input and returns a list of documents that match the query.

    - **query**: The search query string
    - **top_k**: The number of documents to return (default 16)
    - **doc_ids**: The ids of reports to search in (default None)
    """
    try:
        result = await search_esg_db.search(
            request.query, request.top_k, request.doc_ids
        )
        return SearchResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
