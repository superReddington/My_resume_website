from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from app.agent.prompts import SYSTEM_PROMPT
from app.core.config import settings
from app.ingest.pipeline import search_chunks

_graph = None


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: str


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


def _latest_question(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return str(message.content or "").strip()
    return ""


def _format_context(hits: list[dict]) -> str:
    if not hits:
        return "（本次检索没有返回任何原文片段。不要编造履历。）"
    parts: list[str] = []
    for index, hit in enumerate(hits, start=1):
        page = hit["page_number"] or "?"
        parts.append(f"[{index}] {hit['filename']} 第{page}页\n{hit['content']}")
    return "\n\n".join(parts)


def retrieve(state: AgentState) -> dict:
    question = _latest_question(state["messages"])
    hits = search_chunks(question) if question else []
    return {"context": _format_context(hits)}


def generate(state: AgentState) -> dict:
    prompt = SYSTEM_PROMPT.replace("{context}", state.get("context") or "")
    response = get_llm().invoke([SystemMessage(content=prompt), *state["messages"]])
    return {"messages": [response]}


def _build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


def get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
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
    result = graph.invoke({"messages": messages, "context": ""})
    final = result["messages"][-1]
    return getattr(final, "content", "") or ""
