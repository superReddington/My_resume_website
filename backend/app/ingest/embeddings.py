from functools import lru_cache

from app.core.config import settings


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if settings.embedding_api_key:
        return _embed_remote(texts)
    return _embed_local(texts)


def _embed_remote(texts: list[str]) -> list[list[float]]:
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.embedding_api_key,
        base_url=settings.embedding_base_url or None,
    )
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


@lru_cache(maxsize=1)
def _local_model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=settings.embedding_model)


def _embed_local(texts: list[str]) -> list[list[float]]:
    vectors = _local_model().embed(texts)
    return [vector.tolist() for vector in vectors]
