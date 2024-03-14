import re
from typing import Optional, Type

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchResults
from pydantic import BaseModel

from src.models.models import PlainSearchRequest


class SearchInternet(BaseTool):
    name = "search_internet_tool"
    description = "Search the internet for the up-to-date information."

    args_schema: Type[BaseModel] = PlainSearchRequest

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool synchronously."""
        search = DuckDuckGoSearchResults()
        results = search.run(query)

        pattern = r"\[snippet: (.*?), title: (.*?), link: (.*?)\]"
        matches = re.findall(pattern, results)

        docs = [
            {"snippet": match[0], "title": match[1], "link": match[2]}
            for match in matches
        ]

        docs_list = []

        for doc in docs:
            docs_list.append(
                {
                    "content": doc["snippet"],
                    "source": "[{}]({})".format(doc["title"], doc["link"]),
                }
            )

        return str(docs_list)

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        search = DuckDuckGoSearchResults()
        results = search.run(query)

        pattern = r"\[snippet: (.*?), title: (.*?), link: (.*?)\]"
        matches = re.findall(pattern, results)

        docs = [
            {"snippet": match[0], "title": match[1], "link": match[2]}
            for match in matches
        ]

        docs_list = []

        for doc in docs:
            docs_list.append(
                {
                    "content": doc["snippet"],
                    "source": "[{}]({})".format(doc["title"], doc["link"]),
                }
            )

        return str(docs_list)
