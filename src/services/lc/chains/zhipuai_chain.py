from langchain_community.chat_models import ChatZhipuAI

from src.config.config import ZHIPUAI_API_KEY, ZHIPUAI_MODEL


def zhipuai_chain_runnable():
    model = ChatZhipuAI(
        api_key=ZHIPUAI_API_KEY,
        model=ZHIPUAI_MODEL,
        temperature=0.1,
        streaming=True,
    )
    return model
