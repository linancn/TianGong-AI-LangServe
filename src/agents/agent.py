import os
from functools import partial

from dotenv import load_dotenv
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.memory import XataChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import DuckDuckGoSearchRun
from langchain.tools.render import format_tool_to_openai_tool
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from pydantic import BaseModel

load_dotenv()

xata_api_key = os.getenv("XATA_API_KEY")
xata_db_url = os.getenv("XATA_DB_URL")


def init_chat_history(session_id: str) -> BaseChatMessageHistory:
    return XataChatMessageHistory(
        session_id=session_id,
        api_key=xata_api_key,
        db_url=xata_db_url,
        table_name="agent_memory",
    )


class InputModel(BaseModel):
    input: str


def openai_agent():
    lc_tools = [DuckDuckGoSearchRun()]
    oai_tools = [format_tool_to_openai_tool(tool) for tool in lc_tools]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4-1106-preview",
    )

    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_tool_messages(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm.bind(tools=oai_tools)
        | OpenAIToolsAgentOutputParser()
    )

    agent_executor = AgentExecutor(agent=agent, tools=lc_tools, verbose=True)

    agent_executor_with_history = RunnableWithMessageHistory(
        agent_executor,  # type: ignore
        partial(init_chat_history, "pipedrive"),
        history_messages_key="history",
    )

    return agent_executor_with_history
