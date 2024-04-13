import asyncio
from typing import Optional

from src.services.lc.tools.search_local_db_tool import SearchLocalDb


async def main():
    docs_list = await SearchLocalDb().arun("项目投资规模是多大？")
    print(docs_list)

# 运行main函数
asyncio.run(main())