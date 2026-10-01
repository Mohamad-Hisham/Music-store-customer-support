# Music Store Customer Support

A LangGraph customer-support workflow for a digital music store. The design follows
the supplied project brief: verify the customer, load long-term memory, route the
request through music and invoice specialists, pause for missing human input, and
save updated preferences.

## Project status

The first step establishes the system design and runnable Python package layout.
Agent prompts, tools, and graph nodes will be implemented incrementally in the
next steps.

## Design

Read [docs/system-design.md](docs/system-design.md) for the component boundaries,
state transitions, and implementation order.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

The default database is the Chinook SQLite schema loaded into memory, matching the
code supplied in the brief. The current supervisor is deterministic so the complete
workflow runs without an API key; the PDF-aligned prompts are ready in
`src/music_support/agents.py` for a later LLM-backed routing layer.

Install the package itself after installing the requirements:

```bash
python -m pip install -e .
```

The Streamlit interface is the recommended way to try the project:

```bash
streamlit run streamlit_app.py
```

## Run

Start an interactive terminal conversation:

```bash
python -m music_support
```

Or provide the first question directly:

```bash
python -m music_support "My phone number is +55 (12) 3923-5555. How much was my most recent purchase? What albums do you have by The Rolling Stones?"
```

When credentials are missing, the graph pauses and asks for a customer ID, email,
or phone number. The CLI resumes the same thread after the answer. Use the same
thread ID in application code for follow-up questions such as `List some songs that
match my preferences?`.

The database is the Chinook sample database. For the PDF scenario, answer the
credential prompt with `+55 (12) 3923-5555`, customer ID `1`, or the matching demo
email `luisg@embraer.com.br`. Personal emails such as `mh191236@gmail.com` are not
in the sample database and will be rejected.

## Test

```bash
python -m pytest -q
```

The tests cover the required Chinook tables, all catalog and invoice tools, mixed
music/invoice routing, missing-credential interrupt/resume, and same-session
preference memory.

## Planned entry points

- `src/music_support/database.py`: Chinook database initialization.
- `src/music_support/state.py`: LangGraph state schema.
- `src/music_support/graph.py`: workflow graph assembly.
- `src/music_support/agents.py`: supervisor and specialist agents.
- `src/music_support/tools/`: database tools exposed to specialists.