from langchain_openai import ChatOpenAI

from src.config.config import OPENAI_API_KEY, OPENAI_MODEL


def openai_chain_runnable():
    model = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0,
        streaming=True,
    )
    return model
