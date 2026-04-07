# ScriptRunner

A terminal-native idle game where your scripts are the controller. Write code, hit an API, earn cycles. The server runs locally — you're the automation layer.

## Setup

**Requirements:** Python 3.11+

### macOS / Linux

```bash
git clone <repo-url>
cd script-runner
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Windows

```bash
git clone <repo-url>
cd script-runner
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

`pip install -e .` installs all dependencies and registers the `scriptrunner` command.

## Running the Game

```bash
scriptrunner start
```

This starts both the server (`http://localhost:8000`) and the TUI dashboard in one command.

> If you want a server-only instance (e.g. to run scripts while the TUI is open elsewhere), use `scriptrunner server`.

## Playing

The game provides a starter script to get you going:

```bash
python player/starter.py
```

From there, write your own scripts to mine cycles, manage entropy, complete missions, and progress through tiers.

See the [Player Guide](player/player-guide.md) for the full API reference, mechanics, and mission walkthroughs.
