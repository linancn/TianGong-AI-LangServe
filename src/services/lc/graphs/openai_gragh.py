from langchain.tools.render import format_tool_to_openai_function
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolExecutor

from src.services.lc.tools import search_internet_tool

tools = [search_internet_tool()]
tool_executor = ToolExecutor(tools)
