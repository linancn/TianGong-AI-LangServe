import weaviate
from weaviate.classes.query import Rerank


def search_weaviate(query: str, top_k: int = 16):
    """
    Performs a similarity search on Weaviate's vector database based on a given query and returns a list of relevant documents.

    :param query: The query to be used for similarity search in Weaviate's vector database.
    :type query: str
    :param top_k: The number of top matching documents to return. Defaults to 16.
    :type top_k: int or None
    :returns: A list of dictionaries, each containing the content and source of the matched documents. The function returns an empty list if 'top_k' is set to 0.
    :rtype: list of dicts

    Function Behavior:
        - Initializes Weaviate with the specified API key and environment.
        - Conducts a similarity search based on the provided query.
        - Extracts and formats the relevant document information before returning.

    Exceptions:
        - This function relies on Weaviate and Python's os library. Exceptions could propagate if there are issues related to API keys, environment variables, or Weaviate initialization.
        - TypeError could be raised if the types of 'query' or 'top_k' do not match the expected types.

    Note:
        - Ensure the Weaviate API key and environment variables are set before running this function.
        - The function uses 'OpenAIEmbeddings' to initialize Weaviate's vector store, which should be compatible with the embeddings in the Weaviate index.
    """

    if top_k == 0:
        return []

    client = weaviate.connect_to_local(host="host.docker.internal", port=8080)

    try:
        tiangong = client.collections.get("Tiangong")
        response_vector = tiangong.query.near_text(query=query, limit=top_k,target_vector="content")
        response_keyword = tiangong.query.bm25(query=query, limit=top_k)
        response_hybrid = tiangong.query.hybrid(query=query, limit=top_k)

    finally:
        client.close()

    # docs_list = []
    # for doc in response.objects:
    #     docs_list.append(
    #         {"content": doc.properties["answer"], "source": doc.properties["source"]}
    #     )

    return response_vector, response_keyword, response_hybrid


query = "项目建设必要性是什么？"
# query = "项目年度碳排放总量及强度是多少"

k = 5
[aa, bb, cc] = search_weaviate(
    query=query,
    top_k=k,
)
print(aa)
