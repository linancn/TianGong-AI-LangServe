from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.config.config import (
    FASTAPI_AUTH,
    FASTAPI_BEARER_TOKEN,
    FASTAPI_MIDDLEWARE_SECRECT_KEY,
)

from src.routers import (
    health_router,
    search_sci_db_router,
    search_education_db_router,
    search_esg_db_router,
    search_patent_db_router,
    search_standard_db_router,
    search_report_db_router,
    search_textbook_db_router,
    wix_oauth_router,
)

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
    dependencies=[Depends(validate_token)] if FASTAPI_AUTH else None,
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

app.include_router(search_sci_db_router.router)
app.include_router(search_education_db_router.router)
app.include_router(search_esg_db_router.router)
app.include_router(search_patent_db_router.router)
app.include_router(search_standard_db_router.router)
app.include_router(search_report_db_router.router)
app.include_router(search_textbook_db_router.router)


oauth_app = FastAPI()

oauth_app.add_middleware(SessionMiddleware, secret_key=FASTAPI_MIDDLEWARE_SECRECT_KEY)

oauth_app.include_router(wix_oauth_router.router)
oauth_app.include_router(health_router.router)


app.mount("/oauth", oauth_app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=7778)
