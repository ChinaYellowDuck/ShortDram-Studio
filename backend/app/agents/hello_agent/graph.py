"""LangGraph state graph definition for the Hello Agent.

This is a minimal example demonstrating how to build a LangGraph state machine
with a single LLM call node.
"""
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class HelloState(TypedDict):
    """State schema for the Hello Agent.

    Attributes:
        messages: Conversation message history.
        greeting: The generated greeting response.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    greeting: str


def create_hello_graph(llm):
    """Create and compile the Hello Agent state graph.

    Args:
        llm: The language model to use.

    Returns:
        Compiled LangGraph state graph.
    """

    def chat_node(state: HelloState) -> dict:
        """Core chat node that generates a response using the LLM.

        Args:
            state: Current agent state.

        Returns:
            Updated state with AI response and greeting.
        """
        system_prompt = (
            "你是一个友好的短剧创作助手。"
            "请用热情、富有创意的语气回应用户的问候或问题。"
            "回复要简洁有趣，不超过3句话。"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            *state["messages"],
        ]

        response = llm.invoke(messages)
        greeting = response.content

        return {
            "messages": [AIMessage(content=greeting)],
            "greeting": greeting,
        }

    # Build the graph
    graph = StateGraph(HelloState)
    graph.add_node("chat", chat_node)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    return graph
