def init_chat_history(destination: str, session_id: str) -> BaseChatMessageHistory:
    return FirestoreChatMessageHistory(
        destination=destination,
        session_id=session_id,
        max_messages=5,
    )


system_message = SYSTEM_MESSAGE.format(warning="", custom_prompt="")
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_message),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# TODO: tools must be updated on each request
api_wrapper = PipedriveAPIWrapper(access_token)
tools = init_tools(api_wrapper, TOOLS, include_custom_fields=True)

llm = create_azure_gpt4()
llm_with_tools = llm.bind(functions=[format_tool_to_openai_function(t) for t in tools])

agent = (
    {
        "input": lambda x: x["input"],
        "history": lambda x: x["history"],
        "agent_scratchpad": lambda x: format_to_openai_function_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIFunctionsAgentOutputParser()
)

executor = AgentExecutor(
    agent=agent,  # type: ignore
    tools=tools,
    max_iterations=15,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
    tags=["pipedrive"],
    # metadata=hints_user,
    verbose=True,
)

executor_with_history = RunnableWithMessageHistory(
    executor,  # type: ignore
    partial(init_chat_history, "pipedrive"),
    history_messages_key="history",
)


class Input(BaseModel):
    input: str


class Output(BaseModel):
    output: str


app = FastAPI(title="LangChain Server", version="1.0")

add_routes(
    app,
    executor_with_history.with_types(input_type=Input, output_type=Output),
    path="/pipedrive",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)