"""Streamlit interface for the music store customer-support graph."""

from __future__ import annotations

import uuid

import streamlit as st
from langgraph.types import Command

from music_support.app import create_support_app


st.set_page_config(
    page_title="EchoDesk | Music Support",
    page_icon="♪",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');

        :root {
            --ink: #173238;
            --muted: #617474;
            --paper: #f5f6f0;
            --panel: #ffffff;
            --sea-glass: #e5eee9;
            --line: #cbdad4;
            --teal: #0b766e;
            --teal-dark: #07544f;
            --coral: #db7258;
        }

        .stApp { background: var(--paper); color: var(--ink); }
        [data-testid="stHeader"] { background: var(--paper); }
        [data-testid="stToolbar"] { right: 1rem; }
        [data-testid="stSidebar"] {
            background: var(--sea-glass);
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] * { color: var(--ink); }
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] small { color: var(--muted) !important; }
        [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
        .block-container { max-width: 1180px; padding: 2.2rem 3.2rem 3.4rem; }
        h1, h2, h3, p, label, button { font-family: 'Space Grotesk', sans-serif; }
        h1 { color: var(--ink); letter-spacing: 0; font-size: clamp(2rem, 4vw, 3.55rem); line-height: 1.03; }
        h2, h3 { letter-spacing: 0; }
        h3 { color: var(--ink); margin-top: 1.35rem; }
        [data-testid="stMarkdownContainer"] p { color: var(--muted); }
        .eyebrow {
            color: var(--teal); font-family: 'DM Mono', monospace; font-size: .72rem;
            letter-spacing: .12em; text-transform: uppercase; margin-bottom: .8rem;
        }
        .hero-copy { max-width: 720px; color: var(--muted); font-size: 1.05rem; line-height: 1.6; }
        .signal {
            display: flex; align-items: center; gap: .55rem; color: var(--muted);
            font-family: 'DM Mono', monospace; font-size: .72rem; text-transform: uppercase;
        }
        .signal-dot { width: 8px; height: 8px; border-radius: 50%; background: #42a36c; }
        .signal-dot.waiting { background: var(--coral); }
        .metric-card {
            background: var(--panel); border: 1px solid var(--line); border-radius: 7px;
            padding: 1rem 1.1rem; min-height: 92px;
        }
        .metric-label { color: var(--muted); font: .68rem 'DM Mono', monospace; text-transform: uppercase; }
        .metric-value { color: var(--ink); font-size: 1.1rem; font-weight: 600; margin-top: .35rem; }
        .route-chip {
            display: inline-block; background: #e1f1ed; color: var(--teal-dark);
            border-radius: 999px; padding: .28rem .6rem; font: .68rem 'DM Mono', monospace;
            text-transform: uppercase;
        }
        .welcome {
            border: 1px solid #e9d9c8; border-left: 4px solid var(--coral);
            background: #fffaf2; border-radius: 0 7px 7px 0; padding: 1rem 1.2rem;
            color: #4c5754; line-height: 1.55; margin: 1.4rem 0 1.7rem;
        }
        div[data-testid="stChatMessage"] { border-bottom: 1px solid var(--line); padding: 1.05rem .25rem; }
        div[data-testid="stChatMessage"] p { line-height: 1.6; }
        .stButton > button {
            border: 1px solid #b9cdc5; border-radius: 6px; background: #f8faf7;
            color: var(--ink) !important; text-align: left; min-height: 2.5rem;
        }
        .stButton > button:hover { border-color: var(--teal); background: #d9ebe5; color: var(--teal-dark) !important; }
        [data-testid="stChatInput"] {
            background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
        }
        [data-testid="stChatInput"] textarea { color: var(--ink); }
        [data-testid="stChatInput"] button { color: var(--teal); }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { color: var(--ink); }
        [data-testid="stSidebar"] hr { border-color: #c7d8d0; }
        [data-testid="stSidebar"] .stCodeBlock { background: #173238; border: 0; }
        code, .mono { font-family: 'DM Mono', monospace; }

        @media (max-width: 800px) {
            .block-container { padding: 1.5rem 1rem 2.5rem; }
            h1 { font-size: 2.5rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_session() -> None:
    if "support_app" not in st.session_state:
        st.session_state.support_app = create_support_app()
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"streamlit-{uuid.uuid4().hex[:10]}"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = ""
    if "last_result" not in st.session_state:
        st.session_state.last_result = {}


def graph_config() -> dict[str, dict[str, str]]:
    return {"configurable": {"thread_id": st.session_state.thread_id}}


def interrupt_prompt(result: dict) -> str:
    interrupts = result.get("__interrupt__", [])
    return str(interrupts[0].value) if interrupts else ""


def submit_turn(text: str) -> None:
    clean_text = text.strip()
    if not clean_text:
        return

    st.session_state.messages.append({"role": "user", "content": clean_text})
    if st.session_state.pending_prompt:
        result = st.session_state.support_app.invoke(Command(resume=clean_text), graph_config())
    else:
        result = st.session_state.support_app.invoke(
            {"messages": [("user", clean_text)]}, graph_config()
        )
    st.session_state.last_result = result
    st.session_state.pending_prompt = interrupt_prompt(result)
    if result.get("final_response"):
        st.session_state.messages.append(
            {"role": "assistant", "content": result["final_response"]}
        )
    elif st.session_state.pending_prompt:
        st.session_state.messages.append(
            {"role": "assistant", "content": st.session_state.pending_prompt}
        )


def reset_session() -> None:
    for key in ("messages", "pending_prompt", "last_result"):
        st.session_state.pop(key, None)
    st.session_state.thread_id = f"streamlit-{uuid.uuid4().hex[:10]}"
    initialize_session()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("<div class='eyebrow'>EchoDesk / Support desk</div>", unsafe_allow_html=True)
        st.markdown("## A calmer way to find the right answer")
        st.caption("Chinook catalog intelligence with verified customer support.")
        st.divider()
        st.markdown("#### Start with a scenario")
        if st.button("Recent purchase", use_container_width=True):
            submit_turn("How much was my most recent purchase?")
        if st.button("Rolling Stones catalog", use_container_width=True):
            submit_turn("What albums do you have by The Rolling Stones?")
        if st.button("Preference follow-up", use_container_width=True):
            submit_turn("List some songs that match my preferences?")
        st.divider()
        st.markdown("#### Demo credentials")
        st.caption("Use one of these Chinook records when verification asks.")
        st.code("Customer ID 1\n+55 (12) 3923-5555\nluisg@embraer.com.br", language="text")
        st.divider()
        if st.button("Start a new session", use_container_width=True):
            reset_session()
            st.rerun()
        st.markdown(
            f"<div class='mono' style='color:#667371;font-size:.68rem'>THREAD {st.session_state.thread_id}</div>",
            unsafe_allow_html=True,
        )


def render_status() -> None:
    result = st.session_state.last_result
    verified = bool(result.get("customer_id"))
    waiting = bool(st.session_state.pending_prompt)
    route = result.get("requested_agents", [])
    route_label = " + ".join(route).replace("_", " ") if route else "Awaiting request"
    cols = st.columns(3)
    values = [
        ("Identity", "Verified" if verified else "Not verified"),
        ("Route", route_label),
        ("Session", "Needs input" if waiting else "Ready"),
    ]
    for column, (label, value) in zip(cols, values):
        column.markdown(
            f"<div class='metric-card'><div class='metric-label'>{label}</div>"
            f"<div class='metric-value'>{value}</div></div>",
            unsafe_allow_html=True,
        )


def render_chat() -> None:
    if not st.session_state.messages:
        st.markdown(
            "<div class='welcome'><strong>Welcome to EchoDesk.</strong><br>"
            "Ask about the music catalog, a purchase, or both in one message. "
            "Verified sessions can continue with preference-aware recommendations.</div>",
            unsafe_allow_html=True,
        )
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    placeholder = (
        "Enter your customer ID, email, or phone..."
        if st.session_state.pending_prompt
        else "Ask about albums, tracks, genres, or purchases..."
    )
    prompt = st.chat_input(placeholder)
    if prompt:
        submit_turn(prompt)
        st.rerun()


def main() -> None:
    inject_styles()
    initialize_session()
    render_sidebar()
    st.markdown("<div class='eyebrow'>Customer intelligence / 01</div>", unsafe_allow_html=True)
    st.title("Music support, with a human pulse.")
    st.markdown(
        "<p class='hero-copy'>One workspace for catalog discovery and purchase history. "
        "The support graph verifies identity before it touches sensitive customer data.</p>",
        unsafe_allow_html=True,
    )
    status = "waiting" if st.session_state.pending_prompt else ""
    label = "Awaiting customer input" if status else "Support graph online"
    st.markdown(
        f"<div class='signal'><span class='signal-dot {status}'></span>{label}</div>",
        unsafe_allow_html=True,
    )
    st.divider()
    render_status()
    st.markdown("### Conversation")
    render_chat()


if __name__ == "__main__":
    main()