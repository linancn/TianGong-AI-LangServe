from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from langserve import add_routes
from starlette.middleware.sessions import SessionMiddleware

from src.config.config import FASTAPI_BEARER_TOKEN, FASTAPI_MIDDLEWARE_SECRECT_KEY
from src.routers import (
    search_academic_db_router,
    search_patent_db_router,
    upload_file_router,
    wix_oauth_router,
)
from src.services.lc.agents.openai_agent import openai_agent_runnable
from src.services.lc.agents.zhipuai_agent import zhipuai_agent_runnable
from src.services.lc.chains.openai_chain import openai_chain_runnable
from src.services.lc.chains.zhipuai_chain import zhipuai_chain_runnable

bearer_scheme = HTTPBearer()


def validate_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if (
        credentials.scheme != "Bearer"
        or credentials.credentials != FASTAPI_BEARER_TOKEN
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return credentials


app = FastAPI(
    title="TianGong AI Server",
    version="1.0",
    description="TianGong AI API Server",
    # dependencies=[Depends(validate_token)],
)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/.well-known", StaticFiles(directory="static"), name="static")

app.include_router(search_academic_db_router.router)
app.include_router(search_patent_db_router.router)
app.include_router(upload_file_router.router)


add_routes(
    app,
    openai_chain_runnable(),
    path="/openai_chain",
)

add_routes(
    app,
    zhipuai_chain_runnable(),
    path="/zhipuai_chain",
)

add_routes(
    app,
    openai_agent_runnable().with_types(input_type=str, output_type=str),
    path="/openai_agent",
)

add_routes(
    app,
    zhipuai_agent_runnable().with_types(input_type=str, output_type=str),
    path="/zhipuai_agent",
)


add_routes

oauth_app = FastAPI()

oauth_app.add_middleware(SessionMiddleware, secret_key=FASTAPI_MIDDLEWARE_SECRECT_KEY)

oauth_app.include_router(wix_oauth_router.router)


app.mount("/oauth", oauth_app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
