from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import XataChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_experimental.tools import PythonREPLTool

from src.config.config import (
    XATA_API_KEY,
    XATA_MEMORY_DB_URL,
    XATA_MEMORY_TABLE_NAME,
    ZHIPUAI_API_KEY,
    ZHIPUAI_MODEL,
)
from src.services.lc.tools.search_academic_db_tool import SearchAcademicDb
from src.services.lc.tools.search_esg_tool import SearchESG
from src.services.lc.tools.search_internet_tool import SearchInternet
from src.services.lc.tools.search_patent_db_tool import SearchPatentDb


def init_chat_history(session_id: str) -> BaseChatMessageHistory:
    return XataChatMessageHistory(
        session_id=session_id,
        api_key=XATA_API_KEY,
        db_url=XATA_MEMORY_DB_URL,
        table_name=XATA_MEMORY_TABLE_NAME,
    )


def zhipuai_agent_runnable():
    lc_tools = [
        SearchInternet(),
        SearchPatentDb(),
        SearchAcademicDb(),
        SearchESG(),
        PythonREPLTool(),
    ]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question""",
            ),
            MessagesPlaceholder(variable_name="history"),
            (
                "human",
                """Question: {input}
Thought:{agent_scratchpad}""",
            ),
        ]
    )

    llm = ChatZhipuAI(
        api_key=ZHIPUAI_API_KEY,
        model_name=ZHIPUAI_MODEL,
        temperature=0.1,
    )

    agent = create_react_agent(llm=llm, tools=lc_tools, prompt=prompt)

    agent_executor = AgentExecutor(
        agent=agent, tools=lc_tools, verbose=True, handle_parsing_errors=True
    )

    agent_executor_with_history = RunnableWithMessageHistory(
        runnable=agent_executor,
        get_session_history=init_chat_history,
        history_messages_key="history",
    )

    return agent_executor_with_history
