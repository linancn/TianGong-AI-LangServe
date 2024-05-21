from fastapi import APIRouter, HTTPException

from src.models.models import SearchAuthorsResult, VectorListSearchRequest
from src.services.standalone import search_academic_db_authors

router = APIRouter()


@router.post(
    "/search_academic_db_authors",
    response_model=SearchAuthorsResult,
    response_description="List of documents matching the query",
)
async def search_vectors(request: VectorListSearchRequest):
    """
    This endpoint allows you to perform a semantic search authors in an academic or professional vector database.
    It takes a list of query strings as input and returns a list of authors that match the query.

    - **query_list**: The search list of query strings
    - **top_k**: The number of documents to return (default 16)
    """
    try:
        authors = await search_academic_db_authors.search(request.query_list, request.top_k)
        return SearchAuthorsResult(authors=authors)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
