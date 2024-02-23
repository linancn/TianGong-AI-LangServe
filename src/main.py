import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from langchain_openai import ChatOpenAI
from langserve import add_routes
from pydantic import BaseModel, validator

from src.agents.agent import openai_agent
from src.services.search_academic_db import SearchSciDb

load_dotenv()

bearer_scheme = HTTPBearer()
BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
assert BEARER_TOKEN is not None


def validate_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if credentials.scheme != "Bearer" or credentials.credentials != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return credentials


class InputModel(BaseModel):
    input: str

    @validator("input")
    def check_input(cls, v):
        if not isinstance(v, str):
            raise ValueError("input must be a string")
        return v


class OutputModel(BaseModel):
    output: str

    @validator("output")
    def check_input(cls, v):
        if not isinstance(v, str):
            raise ValueError("output must be a string")
        return v


class DocumentQueryModel(BaseModel):
    query: str
    top_k: Optional[int] = 16


class Document(BaseModel):
    content: str
    source: str


app = FastAPI(
    title="TianGong AI Server",
    version="1.0",
    description="TianGong AI API Server",
    dependencies=[Depends(validate_token)],
)

app.mount("/.well-known", StaticFiles(directory="static"), name="static")


@app.post(
    "/vector_search/",
    response_model=List[Document],
    response_description="List of documents matching the query",
)
async def vector_search(doc_query: DocumentQueryModel):
    """
    This endpoint allows you to perform a semantic search in an academic or professional vector database.
    It takes a query string as input and returns a list of documents that match the query.

    - **query**: The search query string
    - **top_k**: The number of documents to return (default 16)
    """
    search = SearchSciDb()
    return await search.search(query=doc_query.query, top_k=doc_query.top_k)


model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"),
    temperature=0,
    streaming=True,
)

add_routes(
    app,
    model,
    path="/openai",
)

add_routes(
    app,
    openai_agent(),
    path="/openai_agent",
    input_type=InputModel,
    output_type=OutputModel,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
