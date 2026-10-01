# Code Map and Runtime Diagrams

## Folder connections

```mermaid
flowchart TB
    UI[streamlit_app.py\nStreamlit UI]
    CLI[src/music_support/__main__.py\nTerminal UI]
    NB[notebooks/music_store_customer_support.ipynb\nNotebook demo]
    APP[src/music_support/app.py\nPublic conversation API]
    GRAPH[src/music_support/graph.py\nLangGraph nodes and edges]
    STATE[src/music_support/state.py\nTyped graph state]
    AGENTS[src/music_support/agents.py\nAgent prompts]
    MEMORY[src/music_support/memory.py\nPreference memory]
    TOOLS[src/music_support/tools/\nRead-only domain queries]
    DB[src/music_support/database.py\nChinook + SQLAlchemy]
    DATA[(Chinook SQLite\nin-memory database)]
    TESTS[tests/test_system.py\nAcceptance tests]

    UI --> APP
    CLI --> APP
    NB --> APP
    APP --> GRAPH
    GRAPH --> STATE
    GRAPH --> MEMORY
    GRAPH --> TOOLS
    GRAPH -. prompt policy .-> AGENTS
    TOOLS --> DB
    DB --> DATA
    TESTS --> APP
    TESTS --> TOOLS
    TESTS --> DB
```

## File responsibilities

| Path | Responsibility | Connects to |
| --- | --- | --- |
| `streamlit_app.py` | Browser UI, chat history, session reset, and interrupt answers. | `app.py` |
| `src/music_support/__main__.py` | Terminal UI for the same workflow. | `app.py` |
| `src/music_support/app.py` | Small public API: create, start, and resume a conversation. | `graph.py`, Streamlit, CLI, notebook |
| `src/music_support/graph.py` | Implements verification, human input, memory load/save, supervisor routing, specialist work, and graph edges. | `state.py`, `memory.py`, `tools/` |
| `src/music_support/state.py` | TypedDict state and LangGraph message reducer. | `graph.py` |
| `src/music_support/agents.py` | The PDF-required role prompts for supervisor, music, and invoice agents. | Future LLM-backed agent layer; routing policy is currently deterministic in `graph.py` |
| `src/music_support/memory.py` | Customer preference store keyed by verified customer ID. | `graph.py` |
| `src/music_support/tools/catalog.py` | Album, track, genre, and song-existence queries. | `database.py` |
| `src/music_support/tools/invoices.py` | Invoice, invoice-line, and employee queries. | `database.py` |
| `src/music_support/database.py` | Downloads the supplied Chinook SQL, builds the in-memory SQLite engine, and exposes safe parameterized reads. | Chinook URL, SQLAlchemy, tools |
| `src/music_support/config.py` | Database URL and model configuration. | `database.py`, agent layer |
| `tests/test_system.py` | Verifies tables, every tool, mixed routing, verification, interruption, memory, and invalid IDs. | All backend layers |
| `notebooks/music_store_customer_support.ipynb` | Human-readable demonstrations of the PDF scenarios. | `app.py`, `database.py` |
| `.streamlit/config.toml` | Streamlit theme and server defaults. | `streamlit_app.py` |
| `requirements.txt` | Runtime, notebook, UI, and test dependencies. | Virtual environment |
| `pyproject.toml` | Installable `src/` package metadata. | Virtual environment |

## Request lifecycle

```mermaid
sequenceDiagram
    actor Customer
    participant UI as Streamlit / CLI / Notebook
    participant API as app.py
    participant Graph as graph.py
    participant DB as database.py + Chinook
    participant Memory as memory.py
    participant Tools as tools/

    Customer->>UI: Ask invoice, catalog, or mixed question
    UI->>API: start_conversation(question, thread_id)
    API->>Graph: invoke state with messages
    Graph->>DB: Verify ID, email, or phone
    alt Missing or invalid credential
        Graph-->>UI: interrupt with human_input request
        Customer->>UI: Provide valid credential
        UI->>API: resume_conversation(answer, thread_id)
        API->>Graph: Command(resume=answer)
        Graph->>DB: Verify again
    end
    Graph->>Memory: Load preferences
    Graph->>Graph: Supervisor selects music, invoice, or both
    Graph->>Tools: Execute read-only specialist queries
    Tools->>DB: Parameterized SQL
    DB-->>Tools: Chinook rows
    Tools-->>Graph: Specialist results
    Graph->>Memory: Save learned preferences
    Graph-->>UI: Final response and updated state
    UI-->>Customer: Display answer
```

## Graph routing

```mermaid
stateDiagram-v2
    [*] --> verify_info
    verify_info --> human_input: missing or invalid credential
    human_input --> verify_info: resume same thread
    verify_info --> load_memory: verified customer
    load_memory --> supervisor
    supervisor --> music_catalog: catalog intent
    supervisor --> invoice_information: purchase intent
    supervisor --> music_catalog: mixed intent, first step
    music_catalog --> supervisor
    supervisor --> invoice_information: mixed intent, remaining step
    invoice_information --> supervisor
    supervisor --> human_input: unclear request
    supervisor --> create_memory: all work complete
    create_memory --> [*]
```

## PDF alignment

- The supplied `sqlite3`, `requests`, `SQLDatabase`, `create_engine`, and
  `StaticPool` setup is in `database.py`.
- The supplied `TypedDict`, `Annotated`, `add_messages`, and `RemainingSteps`
  state pattern is in `state.py`.
- The requested catalog and invoice function names are preserved in `tools/`.
- Verification accepts customer ID, email, and phone, mapping credentials to the
  canonical database customer ID before invoice access.
- Memory is loaded before routing and saved after the response.
- Human-in-the-loop uses LangGraph `interrupt` and `Command(resume=...)`.
- Mixed questions run both specialist paths before `create_memory` finalizes the
  answer.