from langchain_core.tools import tool

from app.ingest.pipeline import search_chunks


@tool
def search_knowledge(query: str) -> str:
    """在简历知识库中检索与问题相关的原文片段。回答个人经历、技能、项目前必须调用。

    Args:
        query: 用中文关键词或完整问句检索，例如「AI 项目」「工作经历」「求职意向」。
    """
    hits = search_chunks(query)
    if not hits:
        return "知识库中没有检索到相关内容。可能尚未上传简历 PDF，或问题与简历无关。"

    parts: list[str] = []
    for index, hit in enumerate(hits, start=1):
        page = hit["page_number"] or "?"
        parts.append(
            f"[{index}] {hit['filename']} 第{page}页\n{hit['content']}"
        )
    return "\n\n".join(parts)
