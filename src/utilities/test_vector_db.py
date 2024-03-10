from src.tools.search_serverless_vector import SearchVectorDB

response = SearchVectorDB().run("什么是物质流分析？")

print(response)