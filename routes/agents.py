from fastapi import APIRouter
from typing import AsyncGenerator
from sse_starlette.sse import EventSourceResponse

import openai
from openbb_ai.models import MessageChunkSSE, QueryRequest
from openbb_ai import get_widget_data, WidgetRequest, message_chunk

from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionSystemMessageParam,
)

from core.agent import execution_loop


agents_router = APIRouter()

@agents_router.post("/openrouter/query")
async def openrouter_query(
    request: QueryRequest) -> EventSourceResponse:
    """Query the OpenRouter."""
    return EventSourceResponse(
        (event.model_dump() async for event in execution_loop(request))
    )

@agents_router.post("/chatglm/query")
async def query(request: QueryRequest) -> EventSourceResponse:
    """Query the Copilot."""

    # We only automatically fetch widget data if the last message is from a
    # human, and widgets have been explicitly added to the request.
    if (
        request.messages[-1].role == "human"
        and request.widgets
        and request.widgets.primary
    ):
        widget_requests: list[WidgetRequest] = []
        for widget in request.widgets.primary:
            widget_requests.append(
                WidgetRequest(
                    widget=widget,
                    input_arguments={
                        param.name: param.current_value for param in widget.params
                    },
                )
            )

        async def retrieve_widget_data():
            yield get_widget_data(widget_requests).model_dump()

        # Early exit to retrieve widget data
        return EventSourceResponse(
            content=retrieve_widget_data(),
            media_type="text/event-stream",
        )

    # Format the messages into a list of OpenAI messages
    openai_messages: list[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(
            role="system",
            content="You are a helpful financial assistant. Your name is 'Vanilla Agent'.",
        )
    ]

    context_str = ""
    for index, message in enumerate(request.messages):
        if message.role == "human":
            openai_messages.append(
                ChatCompletionUserMessageParam(role="user", content=message.content)
            )
        elif message.role == "ai":
            if isinstance(message.content, str):
                openai_messages.append(
                    ChatCompletionAssistantMessageParam(
                        role="assistant", content=message.content
                    )
                )
        # We only add the most recent tool call / widget data to context.  We do
        # this **only for this particular example** to prevent
        # previously-retrieved widget data from piling up and exceeding the
        # context limit of the LLM.
        elif message.role == "tool" and index == len(request.messages) - 1:
            context_str += "Use the following data to answer the question:\n\n"
            result_str = "--- Data ---\n"
            for result in message.data:
                for item in result.items:
                    result_str += f"{item.content}\n"
                    result_str += "------\n"
            context_str += result_str

    if context_str:
        openai_messages[-1]["content"] += "\n\n" + context_str  # type: ignore

    # Define the execution loop.
    async def execution_loop() -> AsyncGenerator[MessageChunkSSE, None]:
        import os
        from dotenv import load_dotenv

        load_dotenv() 
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        OPENAI_MODEL = os.environ.get("OPENAI_MODEL")
        OPENAI_BASE_URL = os.environ.get("BASE_URL")
        client = openai.AsyncOpenAI(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY,
        )
        async for event in await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=openai_messages,
            stream=True,
        ):
            if chunk := event.choices[0].delta.content:
                yield message_chunk(chunk).model_dump()

    # Stream the SSEs back to the client.
    return EventSourceResponse(
        content=execution_loop(),
        media_type="text/event-stream",
    )
