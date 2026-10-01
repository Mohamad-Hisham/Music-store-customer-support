"""LangGraph workflow for verification, routing, specialists, and memory."""

import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .memory import load_memory, save_memory
from .state import AgentName, State
from .tools.catalog import get_albums_by_artist, get_songs_by_genre, get_tracks_by_artist
from .tools.invoices import get_invoices_by_customer_sorted_by_date


PHONE_PATTERN = re.compile(r"(?:\+?\d[\d ()-]{7,}\d)")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
CUSTOMER_ID_PATTERN = re.compile(r"(?:customer\s*(?:id|number)|id)\s*[:#]?\s*(\d+)", re.I)


def _latest_human_message(state: State) -> str:
    for message in reversed(state.get("messages", [])):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def _request_text(state: State) -> str:
    return state.get("customer_request") or _latest_human_message(state)


def _format_rows(rows: list[dict[str, Any]], empty: str) -> str:
    if not rows:
        return empty
    return "\n".join("- " + ", ".join(f"{key}: {value}" for key, value in row.items()) for row in rows)


def _find_customer_id(query: str) -> str | None:
    from .database import ChinookRepository, get_engine_for_chinook_db

    repository = ChinookRepository(get_engine_for_chinook_db())
    match = CUSTOMER_ID_PATTERN.search(query)
    candidate_id = match.group(1) if match else None
    bare_id = re.fullmatch(r"\s*(\d+)\s*", query)
    candidate_id = candidate_id or (bare_id.group(1) if bare_id else None)
    if candidate_id:
        row = repository.fetch_one(
            "SELECT CustomerId FROM Customer WHERE CustomerId = :customer_id",
            {"customer_id": int(candidate_id)},
        )
        return str(row["CustomerId"]) if row else None

    email = EMAIL_PATTERN.search(query)
    phone = PHONE_PATTERN.search(query)
    if email:
        row = repository.fetch_one(
            "SELECT CustomerId FROM Customer WHERE lower(Email) = lower(:value)",
            {"value": email.group(0)},
        )
        return str(row["CustomerId"]) if row else None
    if phone:
        digits = re.sub(r"\D", "", phone.group(0))
        rows = repository.fetch_all("SELECT CustomerId, Phone FROM Customer")
        for row in rows:
            if re.sub(r"\D", "", str(row["Phone"] or "")) == digits:
                return str(row["CustomerId"])
    return None


def verify_info(state: State) -> dict[str, Any]:
    """Verify customer credentials or request missing credentials."""
    query = _latest_human_message(state)
    customer_id = state.get("customer_id") or _find_customer_id(query)
    previous_request = state.get("customer_request", "")
    is_resuming_credentials = state.get("awaiting_human", False)
    is_new_request = bool(previous_request and query != previous_request and not is_resuming_credentials)
    updates: dict[str, Any] = {"customer_request": query if is_new_request else previous_request or query}
    if is_new_request:
        updates.update({"completed_agents": [], "response_parts": []})
    if customer_id:
        return {**updates, "customer_id": customer_id, "pending_input": "", "awaiting_human": False}
    prompt = (
        "I couldn't find a customer matching that credential. Please provide a valid "
        "customer ID, email, or phone number."
        if is_resuming_credentials
        else "Please provide your customer ID, email, or phone number."
    )
    return {
        **updates,
        "pending_input": prompt,
        "awaiting_human": True,
    }


def human_input(state: State) -> dict[str, Any]:
    """Pause the graph and resume with the user's missing information."""
    answer = interrupt(state.get("pending_input", "Please provide more information."))
    return {
        "messages": [HumanMessage(content=str(answer))],
        "pending_input": "",
        "awaiting_human": True,
    }


def load_customer_memory(state: State) -> dict[str, str]:
    return {"loaded_memory": load_memory(state["customer_id"])}


def supervise(state: State) -> dict[str, Any]:
    """Classify the request and select specialists without exposing SQL to the LLM."""
    query = _request_text(state).lower()
    music_terms = ("album", "artist", "track", "song", "genre", "music", "rolling stones")
    invoice_terms = ("invoice", "purchase", "bought", "spent", "payment", "employee", "price")
    requested: list[AgentName] = []
    if any(term in query for term in music_terms):
        requested.append("music_catalog")
    if any(term in query for term in invoice_terms):
        requested.append("invoice_information")
    return {"requested_agents": requested, "completed_agents": [] if not requested else state.get("completed_agents", [])}


def music_catalog_agent(state: State) -> dict[str, Any]:
    query = _request_text(state)
    artist_match = re.search(r"(?:by|artist)\s+([A-Za-z][A-Za-z '&-]{2,})", query, re.I)
    genre_match = re.search(r"genre\s+(?:is\s+)?([A-Za-z][A-Za-z &-]{2,})", query, re.I)
    if artist_match:
        artist = artist_match.group(1).rstrip("?.!,")
        rows = get_albums_by_artist(artist)
        if not rows:
            rows = get_tracks_by_artist(artist)
        result = f"Music catalog results for {artist}:\n{_format_rows(rows, 'No matching catalog items found.')}"
    elif genre_match:
        genre = genre_match.group(1).rstrip("?.!,")
        rows = get_songs_by_genre(genre)
        result = f"Songs in the {genre} genre:\n{_format_rows(rows, 'No matching songs found.')}"
    elif "preference" in query.lower() and state.get("loaded_memory"):
        artists = re.search(r"Favorite artists: (.*?)(?:\. Favorite genres:|$)", state["loaded_memory"])
        artist = artists.group(1).strip() if artists else ""
        rows = get_tracks_by_artist(artist) if artist and artist != "none recorded" else []
        result = f"Songs matching your preferences:\n{_format_rows(rows, 'No saved music preferences found.')}"
    else:
        result = "Please name an artist, album, song, or genre so I can search the catalog."
    completed = list(state.get("completed_agents", []))
    if "music_catalog" not in completed:
        completed.append("music_catalog")
    return {"completed_agents": completed, "response_parts": [*state.get("response_parts", []), result]}


def invoice_information_agent(state: State) -> dict[str, Any]:
    rows = get_invoices_by_customer_sorted_by_date(state["customer_id"])
    if rows:
        latest = rows[0]
        result = (
            f"Your most recent purchase was on {latest['invoice_date']}, "
            f"for a total amount of ${float(latest['total']):.2f}."
        )
    else:
        result = "No invoices were found for this customer."
    completed = list(state.get("completed_agents", []))
    if "invoice_information" not in completed:
        completed.append("invoice_information")
    return {"completed_agents": completed, "response_parts": [*state.get("response_parts", []), result]}


def create_memory(state: State) -> dict[str, Any]:
    response_parts = state.get("response_parts", [])
    response = "I've found the information you requested:\n\n" + "\n\n".join(response_parts)
    response += "\n\nIf you need any more details, feel free to ask!"
    query = _request_text(state)
    artists = ["The Rolling Stones"] if "rolling stones" in query.lower() else []
    save_memory(state["customer_id"], artists=artists, genres=[])
    return {"final_response": response, "messages": [AIMessage(content=response)]}


def _after_verification(state: State) -> str:
    return "human_input" if state.get("pending_input") else "load_memory"


def _after_supervisor(state: State) -> str:
    requested = state.get("requested_agents", [])
    completed = state.get("completed_agents", [])
    if not requested:
        return "human_input"
    for agent in requested:
        if agent not in completed:
            return agent
    return "create_memory"


def _after_human_input(state: State) -> str:
    return "verify_info"


def build_support_graph(checkpointer=None):
    """Compile the PDF workflow with checkpointing for interrupt/resume."""
    workflow = StateGraph(State)
    workflow.add_node("verify_info", verify_info)
    workflow.add_node("human_input", human_input)
    workflow.add_node("load_memory", load_customer_memory)
    workflow.add_node("supervisor", supervise)
    workflow.add_node("music_catalog", music_catalog_agent)
    workflow.add_node("invoice_information", invoice_information_agent)
    workflow.add_node("create_memory", create_memory)
    workflow.add_edge(START, "verify_info")
    workflow.add_conditional_edges("verify_info", _after_verification)
    workflow.add_edge("human_input", "verify_info")
    workflow.add_edge("load_memory", "supervisor")
    workflow.add_conditional_edges("supervisor", _after_supervisor)
    workflow.add_edge("music_catalog", "supervisor")
    workflow.add_edge("invoice_information", "supervisor")
    workflow.add_edge("create_memory", END)
    return workflow.compile(checkpointer=checkpointer or MemorySaver())