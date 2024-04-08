import os

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.memory import XataChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools import E2BDataAnalysisTool
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import ChatOpenAI

from src.config.config import (
    E2B_API_KEY,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    XATA_API_KEY,
    XATA_MEMORY_DB_URL,
    XATA_MEMORY_TABLE_NAME,
)


def init_chat_history(session_id: str) -> BaseChatMessageHistory:
    return XataChatMessageHistory(
        session_id=session_id,
        api_key=XATA_API_KEY,
        db_url=XATA_MEMORY_DB_URL,
        table_name=XATA_MEMORY_TABLE_NAME,
    )


def save_artifact(artifact):
    print("New matplotlib chart generated:", artifact.name)
    # Download the artifact as `bytes` and leave it up to the user to display them (on frontend, for example)
    file = artifact.download()
    basename = os.path.basename(artifact.name)

    # Save the chart to the `charts` directory
    with open(f"./charts/{basename}", "wb") as f:
        f.write(file)


e2b_data_analysis_tool = E2BDataAnalysisTool(
    # Pass environment variables to the sandbox
    api_key=E2B_API_KEY,
    env_vars={"MY_SECRET": "secret_value"},
    on_stdout=lambda stdout: print("stdout:", stdout),
    on_stderr=lambda stderr: print("stderr:", stderr),
    on_artifact=save_artifact,
)


def openai_data_analysis_runnable():
    lc_tools = [e2b_data_analysis_tool.as_tool()]
    oai_tools = [convert_to_openai_function(tool) for tool in lc_tools]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_input}"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{human_input}"),
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
            "system_input": lambda x: x["system_input"],
            "human_input": lambda x: x["human_input"],
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
