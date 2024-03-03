import os
import uuid
from typing import List, Optional

import redis
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_openai import ChatOpenAI
from langserve import add_routes
from pydantic import BaseModel, validator
from starlette.middleware.sessions import SessionMiddleware

from src.agents.agent import openai_agent
from src.services.wix_oauth import (
    get_member_access_token,
    wix_get_callback_url,
    wix_get_subscription,
)
from src.tools.search_academic_db import SearchSciDb

load_dotenv()

bearer_scheme = HTTPBearer()
BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
assert BEARER_TOKEN is not None

r = redis.Redis(host="localhost", port=6379, db=0)


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

oauth_app = FastAPI()
templates = Jinja2Templates(directory="templates")
oauth_app.add_middleware(
    SessionMiddleware, secret_key=os.environ.get("MIDDLEWARE_SECRECT_KEY")
)


def get_oauth_params(
    response_type: str = Query(...),
    client_id: str = Query(...),
    scope: str = Query(...),
    state: str = Query(...),
    redirect_uri: str = Query(...),
) -> dict:
    return {
        "response_type": response_type,
        "client_id": client_id,
        "scope": scope,
        "state": state,
        "redirect_uri": redirect_uri,
    }


async def get_session_data(request: Request):
    return request.session


@oauth_app.get("/login/")
async def login(
    request: Request,
    oauth_params: dict = Depends(get_oauth_params),
    session_data: dict = Depends(get_session_data),
):
    session_data.update(oauth_params)
    return templates.TemplateResponse("login.html", {"request": request})


@oauth_app.post("/login/")
async def login_post(
    username: str = Form(...),
    password: str = Form(...),
    session_data: dict = Depends(get_session_data),
):
    # response_type = session_data.get("response_type")
    # client_id = session_data.get("client_id")
    # scope = session_data.get("scope")
    state = session_data.get("state")
    # redirect_uri = session_data.get("redirect_uri")

    wix_callback_url, code_verifier = await wix_get_callback_url(
        username=username, password=password, state=state
    )

    session_data["wix_callback_url"] = wix_callback_url
    session_data["code_verifier"] = code_verifier

    # redirect to callback url
    url = f"../callback/"
    raise HTTPException(
        status_code=status.HTTP_303_SEE_OTHER, headers={"Location": url}
    )


@oauth_app.get("/callback/")
async def callback(request: Request, session_data: dict = Depends(get_session_data)):
    wix_callback_url = session_data.get("wix_callback_url")

    return templates.TemplateResponse(
        "callback.html",
        {
            "request": request,
            "wix_callback_url": wix_callback_url,
        },
    )


class SubscriptionRequest(BaseModel):
    code: str
    state: str


@oauth_app.post("/callback/")
async def subscription(
    request: SubscriptionRequest, session_data: dict = Depends(get_session_data)
):
    # response_type = session_data.get("response_type")
    # client_id = session_data.get("client_id")
    # scope = session_data.get("scope")
    state = session_data.get("state")
    redirect_uri = session_data.get("redirect_uri")
    # state from wix
    openai_code = str(uuid.uuid4())
    url = redirect_uri + f"?state={state}&code={openai_code}"

    wix_code = request.code

    member_access_token = await get_member_access_token(
        wix_code, session_data["code_verifier"]
    )

    subscription, expires_in = await wix_get_subscription(member_access_token)

    r.set(openai_code, expires_in)

    if subscription == "Pro":
        return JSONResponse(content={"message": "You are an Pro member.", "url": url})

    else:
        return JSONResponse(
            content={
                "message": "You are not an Pro member.",
                "url": "https://www.kaiwu.info",
            }
        )


@oauth_app.post("/authorization/")
async def authorization(
    client_id: str = Form(...),
    client_secret: str = Form(...),
    code: str = Form(...),
):
    expires_in = int(r.get(code))
    if (
        client_id != os.environ.get("CLIENT_ID")
        or client_secret != os.environ.get("CLIENT_SECRET")
        or expires_in is None
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    print(expires_in)
    return {
        "access_token": os.environ.get("BEARER_TOKEN"),
        "token_type": "bearer",
        "expires_in": expires_in,
    }


app.mount("/oauth", oauth_app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
