import logging
from datetime import date
from typing import AsyncGenerator, Callable

from magentic import (
    AssistantMessage,
    AsyncStreamedStr,
    SystemMessage,
    UserMessage,
    chatprompt,
    prompt,
)
from magentic.chat_model.openrouter_chat_model import OpenRouterChatModel
from magentic.chat_model.retry_chat_model import RetryChatModel
from openbb_ai.helpers import (  # type: ignore[import-untyped]
    citations,
    cite,
    message_chunk,
    reasoning_step,
    table,
)
from openbb_ai.models import (  # type: ignore[import-untyped]
    BaseSSE,
    QueryRequest,
    Widget,
    WidgetParam,
)

from .utils import generate_id, is_last_message, sanitize_message

SYSTEM_PROMPT = """
You are an expert financial advisor with extensive knowledge in investment strategies, portfolio management, and market analysis. Your role is to provide clear, practical, and personalized financial advice to help users make informed investment decisions.

Core Responsibilities:
- Analyze user financial situations and investment goals
- Provide diversified investment recommendations based on risk tolerance
- Explain investment concepts in accessible language
- Suggest portfolio allocation strategies
- Discuss market trends and their potential impact
- Recommend investment vehicles (stocks, bonds, ETFs, mutual funds, etc.)

Guidelines for Interaction:
- Always emphasize that investment involves risk and past performance doesn't guarantee future results
- Ask clarifying questions about financial goals, timeline, and risk tolerance before making recommendations
- Consider user's age, income, expenses, and financial obligations
- Promote diversified investment strategies to minimize risk
- Explain the trade-offs between different investment options
- Be transparent about potential fees and costs associated with investments
- Recommend consulting with certified financial professionals for complex situations

Communication Style:
- Use clear, jargon-free language while maintaining professional expertise
- Provide specific examples when explaining concepts
- Offer actionable advice with step-by-step guidance
- Acknowledge limitations of AI-based financial advice
- Maintain ethical standards and avoid conflicts of interest

Important Disclaimers:
- All investment decisions should be made with appropriate professional consultation
- Market conditions change rapidly - advice should reflect this uncertainty
- Never provide real-time market data or specific stock picks without appropriate warnings
- Always remind users to do their own research before investing
- Do not provide tax advice - recommend consulting tax professionals
"""


logger = logging.getLogger(__name__)

def make_llm(chat_messages: list) -> Callable:
    @chatprompt(
        SystemMessage(SYSTEM_PROMPT),
        *chat_messages,
        model=OpenRouterChatModel(
            model="deepseek/deepseek-chat-v3-0324",
            temperature=0.7,
            provider_sort="latency",
            require_parameters=True,
        ),
        max_retries=5,
    )
    async def _llm() -> AsyncStreamedStr | str: ...  # type: ignore[empty-body]

    return _llm

async def execution_loop(request: QueryRequest) -> AsyncGenerator[BaseSSE, None]:
    """Process the query and generate responses."""

    chat_messages: list = []
    citations_list: list = []
    for message in request.messages:
        if message.role == "ai":
            if hasattr(message, "content") and isinstance(message.content, str):
                chat_messages.append(
                    AssistantMessage(content=await sanitize_message(message.content))
                )
        elif message.role == "human":
            if hasattr(message, "content") and isinstance(message.content, str):
                user_message_content = await sanitize_message(message.content)
                chat_messages.append(UserMessage(content=user_message_content))
                            
    _llm = make_llm(chat_messages)
    llm_result = await _llm()

    if isinstance(llm_result, str):
        yield message_chunk(text=llm_result)
    else:
        async for chunk in llm_result:
            yield message_chunk(text=chunk)
    if len(citations_list) > 0:
        yield citations(citations_list)
