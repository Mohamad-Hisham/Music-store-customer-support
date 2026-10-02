from music_support.database import get_engine_for_chinook_db, required_tables
from music_support.graph import build_support_graph
from music_support.tools.catalog import get_albums_by_artist, get_songs_by_genre
from music_support.tools.catalog import check_for_songs, get_tracks_by_artist
from music_support.tools.invoices import (
    get_employee_by_invoice_and_customer,
    get_invoices_by_customer_sorted_by_date,
    get_invoices_sorted_by_unit_price,
)
from langgraph.types import Command


def test_chinook_schema_and_catalog_tools():
    engine = get_engine_for_chinook_db()
    assert {"Customer", "Invoice", "Artist", "Album", "Track", "Employee"} <= required_tables(engine)
    albums = get_albums_by_artist("Rolling Stones")
    assert albums
    assert any("Rolling" in row["artist"] for row in albums)
    assert get_songs_by_genre("Rock")
    tracks = get_tracks_by_artist("Rolling Stones")
    assert tracks
    assert check_for_songs(tracks[0]["track"])


def test_invoice_tool_returns_customer_history():
    rows = get_invoices_by_customer_sorted_by_date("1")
    assert rows
    assert rows[0]["total"] is not None
    assert get_invoices_sorted_by_unit_price("1")
    employee = get_employee_by_invoice_and_customer(str(rows[0]["invoice_id"]), "1")
    assert employee and employee["last_name"]


def test_mixed_query_completes_for_phone_customer():
    app = build_support_graph()
    result = app.invoke(
        {"messages": [("user", "My phone number is +55 (12) 3923-5555. How much was my most recent purchase? What albums do you have by The Rolling Stones?")]},
        {"configurable": {"thread_id": "mixed-test"}},
    )
    assert result["final_response"]
    assert "purchase" in result["final_response"]
    assert "Music catalog" in result["final_response"]


def test_missing_credentials_interrupt_and_resume():
    app = build_support_graph()
    config = {"configurable": {"thread_id": "missing-credentials-test"}}
    paused = app.invoke(
        {"messages": [("user", "How much was my most recent purchase?")]},
        config,
    )
    assert paused["__interrupt__"]
    resumed = app.invoke(
        Command(resume="Customer ID: 1"),
        config,
    )
    assert "most recent purchase" in resumed["final_response"]


def test_invalid_credentials_prompt_again():
    app = build_support_graph()
    config = {"configurable": {"thread_id": "invalid-credentials-test"}}
    app.invoke({"messages": [("user", "How much was my most recent purchase?")]}, config)
    paused = app.invoke(Command(resume="not a customer credential"), config)
    assert paused["__interrupt__"]
    assert "couldn't find" in paused["__interrupt__"][0].value


def test_bare_customer_id_is_accepted():
    app = build_support_graph()
    result = app.invoke(
        {"messages": [("user", "How much was my most recent purchase?")]},
        {"configurable": {"thread_id": "bare-id-test"}},
    )
    result = app.invoke(
        Command(resume="1"),
        {"configurable": {"thread_id": "bare-id-test"}},
    )
    assert "most recent purchase" in result["final_response"]


def test_unknown_customer_id_is_rejected():
    app = build_support_graph()
    config = {"configurable": {"thread_id": "unknown-id-test"}}
    app.invoke({"messages": [("user", "How much was my most recent purchase?")]}, config)
    paused = app.invoke(Command(resume="999999"), config)
    assert paused["__interrupt__"]
    assert "couldn't find" in paused["__interrupt__"][0].value


def test_follow_up_uses_saved_preferences_in_same_thread():
    app = build_support_graph()
    config = {"configurable": {"thread_id": "preference-follow-up-test"}}
    first = app.invoke(
        {"messages": [("user", "My phone number is +55 (12) 3923-5555. What albums do you have by The Rolling Stones?")]},
        config,
    )
    assert "The Rolling Stones" in first["final_response"]
    second = app.invoke(
        {"messages": [("user", "List some songs that match my preferences?")]},
        config,
    )
    assert "Songs matching your preferences" in second["final_response"]
    assert "The Rolling Stones" in second["final_response"]


def test_singular_rolling_stone_request_saves_preference():
    app = build_support_graph()
    config = {"configurable": {"thread_id": "singular-preference-test"}}
    first = app.invoke(
        {"messages": [("user", "My phone number is +55 (12) 3923-5555. What albums do you have by Rolling Stone?")]},
        config,
    )
    assert "Music catalog results" in first["final_response"]
    second = app.invoke(
        {"messages": [("user", "List some songs that match my preferences?")]},
        config,
    )
    assert "Songs matching your preferences" in second["final_response"]
    assert "track:" in second["final_response"]