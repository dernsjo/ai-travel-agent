from langchain_openai import ChatOpenAI

from agent.dependencies import settings


def get_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        openai_api_key=settings.openai_api_key,
        temperature=0.3,
    )
