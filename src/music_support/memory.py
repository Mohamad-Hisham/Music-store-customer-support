"""Small in-memory long-term preference store for the first milestone."""

from collections import defaultdict


_MEMORY: dict[str, dict[str, list[str]]] = defaultdict(
    lambda: {"artists": [], "genres": []}
)


def load_memory(customer_id: str) -> str:
    """Serialize known preferences for a customer."""
    preferences = _MEMORY[customer_id]
    artists = ", ".join(preferences["artists"]) or "none recorded"
    genres = ", ".join(preferences["genres"]) or "none recorded"
    return f"Favorite artists: {artists}. Favorite genres: {genres}."


def save_memory(customer_id: str, *, artists: list[str], genres: list[str]) -> None:
    """Merge newly learned preferences into the customer's memory."""
    for key, values in (("artists", artists), ("genres", genres)):
        for value in values:
            if value not in _MEMORY[customer_id][key]:
                _MEMORY[customer_id][key].append(value)