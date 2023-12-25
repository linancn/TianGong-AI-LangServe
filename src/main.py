from fastapi import FastAPI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langserve import add_routes
from pydantic import BaseModel, validator

from agents.agent import openai_agent


class InputModel(BaseModel):
    input: str

    @validator("input")
    def check_input(cls, v):
        if not isinstance(v, str):
            raise ValueError("input must be a string")
        return v


app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple api server using Langchain's Runnable interfaces",
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
