from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.memory import XataChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_experimental.tools import PythonREPLTool
from langchain_openai import ChatOpenAI

from src.config.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    XATA_API_KEY,
    XATA_MEMORY_DB_URL,
    XATA_MEMORY_TABLE_NAME,
)
from src.services.lc.tools.search_academic_db_tool import SearchAcademicDb
from src.services.lc.tools.search_esg_tool import SearchESG
from src.services.lc.tools.search_internet_tool import SearchInternet
from src.services.lc.tools.search_local_db_tool import SearchLocalDb
from src.services.lc.tools.search_patent_db_tool import SearchPatentDb


def init_chat_history(session_id: str) -> BaseChatMessageHistory:
    return XataChatMessageHistory(
        session_id=session_id,
        api_key=XATA_API_KEY,
        db_url=XATA_MEMORY_DB_URL,
        table_name=XATA_MEMORY_TABLE_NAME,
    )


def openai_agent_runnable():
    lc_tools = [
        SearchInternet(),
        SearchPatentDb(),
        SearchAcademicDb(),
        SearchESG(),
        SearchLocalDb(),
        PythonREPLTool(),
    ]
    oai_tools = [convert_to_openai_function(tool) for tool in lc_tools]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are helpful AI assistant."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        temperature=0,
        model=OPENAI_MODEL,
    )

    agent = (
        {
            "input": lambda x: x["input"],
            "history": lambda x: x["history"],
            "agent_scratchpad": lambda x: format_to_openai_tool_messages(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm.bind_tools(tools=oai_tools)
        | OpenAIToolsAgentOutputParser()
    )

    agent_executor = AgentExecutor(
        agent=agent, tools=lc_tools, verbose=True, handle_parsing_errors=True
    )

    agent_executor_with_history = RunnableWithMessageHistory(
        runnable=agent_executor,
        get_session_history=init_chat_history,
        history_messages_key="history",
    )

    return agent_executor_with_history
