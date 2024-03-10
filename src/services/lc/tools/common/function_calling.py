from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI


def function_calling(
    function_desc: str,
    function_para: dict,
    prompt: ChatPromptTemplate,
    openai_api_key: str,
    openai_model_name: str,
    query: str,
):
    function = {
        "name": "function_calling",
        "description": function_desc,
        "parameters": function_para,
    }
    model = ChatOpenAI(
        api_key=openai_api_key, model=openai_model_name, temperature=0
    ).bind(function_call={"name": "function_calling"}, functions=[function])
    runnable = {"input": RunnablePassthrough()} | prompt | model

    # query = query.encode("utf-8").decode("unicode_escape")

    response = runnable.invoke(query)

    result = response.additional_kwargs["function_call"]["arguments"]

    return result
