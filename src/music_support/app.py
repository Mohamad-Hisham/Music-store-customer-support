"""Convenience API for running support conversations."""

from langgraph.types import Command

from .graph import build_support_graph


def create_support_app():
    """Create a checkpointed support graph."""
    return build_support_graph()


def start_conversation(app, question: str, thread_id: str = "demo"):
    """Start a conversation and return the graph result or interrupt payload."""
    return app.invoke(
        {"messages": [("user", question)]},
        {"configurable": {"thread_id": thread_id}},
    )


def resume_conversation(app, answer: str, thread_id: str = "demo"):
    """Resume a paused conversation with human input."""
    return app.invoke(
        Command(resume=answer),
        {"configurable": {"thread_id": thread_id}},
    )