from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from langchain.messages import HumanMessage, SystemMessage

from agent.llm_provider import get_llm
from agent.system_prompt import system_prompt
from agent.tools import flight_search, hotel_search


def create_travel_agent():
    """Create and return a travel agent executor."""
    agent = create_agent(
        model=get_llm(),
        tools=[flight_search, hotel_search],
        system_prompt=system_prompt(),
        checkpointer=InMemorySaver()
        )
    return agent

agent = create_travel_agent()

def run_agent(user_input: str, thread_id: str = "1") -> str:
    """Run the agent with user input and optional chat history."""
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    response = agent.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
    reply = response["messages"][-1].content
    return reply