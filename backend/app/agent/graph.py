from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import search_knowledge
from app.core.config import settings

_graph = None


def get_llm() -> ChatOpenAI:
    if not settings.deepseek_api_key:
        raise RuntimeError("请在 .env 中设置 DEEPSEEK_API_KEY")
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.2,
        streaming=True,
    )


def get_graph():
    global _graph
    if _graph is None:
        _graph = create_react_agent(
            get_llm(),
            tools=[search_knowledge],
            prompt=SYSTEM_PROMPT,
        )
    return _graph


def to_langchain_messages(history: list[dict]) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for item in history:
        role = item.get("role")
        content = item.get("content") or ""
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def run_once(question: str, history: list[dict] | None = None) -> str:
    graph = get_graph()
    messages = to_langchain_messages(history or [])
    messages.append(HumanMessage(content=question))
    result = graph.invoke({"messages": messages})
    final = result["messages"][-1]
    return getattr(final, "content", "") or ""
