import os

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain.chat_models import ChatOpenAI
from langserve import add_routes
from pydantic import BaseModel, validator

from src.agents.agent import openai_agent

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


app = FastAPI(
    title="TianGong AI Server",
    version="1.0",
    description="TianGong AI API Server",
    dependencies=[Depends(validate_token)],
)

model = ChatOpenAI(
    model="gpt-4-1106-preview",
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
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
