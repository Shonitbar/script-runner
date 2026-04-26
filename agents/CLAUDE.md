# CLAUDE.md — ScriptRunner Developer Guide

## Project Overview

ScriptRunner is a terminal-native idle/clicker game where players write Python scripts to call a local HTTP API (FastAPI server at `localhost:8000`). The server maintains all game state, enforces mechanics, and broadcasts real-time updates via WebSocket. A Textual TUI dashboard visualizes live state.

**Entry point:** `scriptrunner start` (server + TUI) or `scriptrunner server` (server only)  
**Player entry point:** `player/starter.py` — a minimal script that calls `/mine` once

---

## Repository Layout

```
scriptrunner/
  cli.py                    # Typer CLI: `start` and `server` commands
  server/
    main.py                 # FastAPI app, route registration, lifespan hook
    db.py                   # SQLite setup, session factory, mission seed data
    models.py               # SQLModel schemas: GameState, Mission, CallLog, Automation
    mission_engine.py       # Auto-completion logic for all 14 missions
    state.py                # Background decay loop: entropy, passive income, volatility
    routes/
      core.py               # /status, /mine, /overclock, /exploit
      compress.py           # /compress
      missions.py           # /missions
      history.py            # /status/history
      automate.py           # /automate (POST register, GET list)
      pipeline.py           # /pipeline (batch ops)
      prestige.py           # /prestige, /prestige/status
      dark_ops.py           # /dark-ops/* (prestige-only secret missions)
      ws.py                 # /ws WebSocket broadcaster
  tui/
    app.py                  # Textual app, WebSocket client, layout
    widgets/
      core_panel.py         # Cycles / entropy / synth / tier stats
      entropy_gauge.py      # Visual entropy bar with risk zone markers
      log_panel.py          # Last 8 API calls
      missions_panel.py     # Mission list
      automations_panel.py  # Automations + overclock countdown
player/
  starter.py                # Minimal player bootstrap (gitignored)
  player-guide.md           # Player-facing API reference and walkthroughs
agents/                     # Internal docs — gitignored
  CLAUDE.md                 # This file
  spec.md                   # Game mechanics spec
```

---

## Running the Project

```bash
# Install (editable, inside venv)
pip install -e .

# Start server + TUI dashboard
scriptrunner start

# Start server only (for headless / testing)
scriptrunner server

# Player script
python player/starter.py
```

Save file location: `~/.scriptrunner/save.db` (SQLite). Delete it to reset game state.

---

## Architecture

### Request Lifecycle
1. FastAPI route handler (in `routes/`) receives request
2. Opens SQLModel DB session via `get_session()` dependency
3. Reads/mutates `GameState` (single row, `id=1`)
4. Appends a `CallLog` record
5. Calls `mission_engine.check_missions(state, session)` to auto-complete any newly satisfied missions
6. Returns JSON response

### Background Loop (`state.py → _decay_loop`)
Runs every 1 second while server is alive:
- `entropy -= 0.1` (floor 0)
- `cycles += 0.5 * len(active_automations) * cycle_multiplier`
- Increments `passive_ticks` (used for "Full Auto" mission)
- Tier 3+: random volatility spikes broadcast over WebSocket

### WebSocket (`routes/ws.py`)
- Clients connect to `/ws`
- Server pushes full state snapshot every 1 second (`type: "state"`)
- Entropy spike events pushed immediately when they fire (`type: "entropy_spike"`)
- TUI connects here for live dashboard updates

### Database (`db.py`)
- Single `GameState` row (id=1), created on first startup
- `Mission` rows seeded from `MISSION_DEFINITIONS` list in `db.py`
- `CallLog` rows appended by every route
- `Automation` rows created via `/automate`

---

## Key Invariants

- **One mine cooldown:** Global `last_mine_time` on `GameState`; server returns 429 if called within 1s.
- **Pipeline still respects cooldown:** Each `mine` op inside `/pipeline` checks the same cooldown.
- **Tier gates:** Routes check `state.tier >= N` before executing. Return 403 if not unlocked.
- **Prestige requirement:** `/prestige` requires `state.synth >= 5`. Resets cycles, tier, missions. Carries `cycle_multiplier × 1.5`.
- **Dark ops gate:** Dark ops endpoints check `state.dark_ops_unlocked`. Only set after first prestige.
- **HMAC puzzle key:** Shards from `/dark-ops/hint/1–5` concatenate to `"scriptrun!"`. Signature for `/dark-ops/finalize` uses HMAC-SHA256.

---

## Mission Engine (`mission_engine.py`)

`check_missions(state, session)` is called after every mutating route. It iterates incomplete missions and checks each `completion_type` against counters on `GameState`:

| completion_type | Checked field(s) |
|---|---|
| `mine_once` | `mines_total >= 1` |
| `mine_n` | `mines_total >= N` |
| `status_n` | `status_calls >= N` |
| `patience` | `patience_mined_twice` flag |
| `accumulate_cycles` | `cycles >= N` |
| `loop_artist` | `mines_total >= 50` |
| `compressor` | `compressor_high_entropy` + compress below 30 |
| `danger_zone` | `danger_zone_mines >= 5` |
| `scheduler` | `scheduler_start` + timing check |
| `scaler` | `cycles >= 5000` |
| `pipeline_engineer` | `pipeline_mines` + `pipeline_compresses` counters |
| `overclock_runner` | `overclock_active` + mines within 30s |
| `full_auto` | `passive_ticks >= 600` |
| `titan` | `cycles >= 50000` |
| `dark_ops_finalize` | Handled inside `/dark-ops/finalize` route directly |

When a mission completes: `mission.completed = True`, cycles and synth rewards applied, `state.tier` updated if the mission unlocks a new tier.

---

## Adding a New Endpoint

1. Create or edit a file in `scriptrunner/server/routes/`
2. Define an `APIRouter` and add route functions
3. Register the router in `scriptrunner/server/main.py` via `app.include_router()`
4. If it has a tier gate, check `state.tier >= N` at the top of the handler and raise `HTTPException(403)`
5. Append a `CallLog` entry at the end of the handler
6. Call `check_missions()` if the operation mutates state

## Adding a New Mission

1. Add a dict entry to `MISSION_DEFINITIONS` in `db.py`
2. Add a new `completion_type` string and any required counter columns to `GameState` in `models.py`
3. Add the check logic in `mission_engine.py` under `check_missions()`
4. Increment relevant counters in the appropriate route handler(s)

---

## Tech Stack

| Layer | Library | Version |
|---|---|---|
| API server | FastAPI + Uvicorn | latest |
| ORM / DB | SQLModel (SQLite) | latest |
| TUI | Textual | latest |
| CLI | Typer | latest |
| Terminal rendering | Rich | latest |
| Player scripts | requests | latest |

Python 3.11+ required.

---

## Common Gotchas

- `GameState` is a single-row table. Always query with `session.get(GameState, 1)` — never create a second row.
- Entropy is a float; compare with `>= 90.0` not `== 90`.
- `cycle_multiplier` starts at `1.0` and multiplies all mine yield and passive income. Don't forget to apply it.
- The TUI connects to WebSocket on startup; if the server isn't running yet, it polls until connected.
- `starter.py` is gitignored intentionally — players should not commit their automation scripts.
