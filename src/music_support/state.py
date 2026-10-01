"""Shared LangGraph state schema."""

from typing import Annotated, Literal

from langgraph.graph.message import AnyMessage, add_messages
from langgraph.managed.is_last_step import RemainingSteps
from typing_extensions import TypedDict


AgentName = Literal["music_catalog", "invoice_information"]


class State(TypedDict, total=False):
    """Represents the state of the LangGraph customer-support workflow."""

    customer_id: str
    customer_request: str
    messages: Annotated[list[AnyMessage], add_messages]
    loaded_memory: str
    pending_input: str
    awaiting_human: bool
    requested_agents: list[AgentName]
    completed_agents: list[AgentName]
    final_response: str
    response_parts: list[str]
    remaining_steps: RemainingSteps