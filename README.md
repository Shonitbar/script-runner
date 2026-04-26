<div align="center">

<img width="400" alt="ScriptRunner TUI" src="https://github.com/user-attachments/assets/6811b50b-37c0-4a28-8fb7-742f5357cd8c" />

# ScriptRunner

**A terminal-native idle game where your scripts are the controller.**  
Write code, hit an API, earn cycles. The server runs locally — you are the automation layer.

[![Stars](https://img.shields.io/github/stars/Shonitbar/script-runner?style=for-the-badge&color=yellow)](https://github.com/Shonitbar/script-runner/stargazers)
[![Forks](https://img.shields.io/github/forks/Shonitbar/script-runner?style=for-the-badge&color=blue)](https://github.com/Shonitbar/script-runner/network/members)
[![License](https://img.shields.io/github/license/Shonitbar/script-runner?style=for-the-badge&color=green)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/Shonitbar/script-runner?style=for-the-badge&color=purple)](https://github.com/Shonitbar/script-runner/commits/main)
[![Python](https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Issues](https://img.shields.io/github/issues/Shonitbar/script-runner?style=for-the-badge&color=red)](https://github.com/Shonitbar/script-runner/issues)

</div>

---

## What Is This?

ScriptRunner is an idle game that runs entirely in your terminal. There is no UI to click through — the server exposes a local REST API and **you write the scripts** that interact with it. The built-in TUI dashboard shows the game state in real time while your automation runs in the background.

Mine cycles, manage entropy, complete missions, and climb through tiers — all from code you write yourself.

---

## Features

- **Script-driven gameplay** — interact with the game through a local HTTP API, no GUI required
- **Live TUI dashboard** — real-time Textual UI showing your current state, resources, and missions
- **Starter script included** — jump straight in without writing from scratch
- **Persistent state** — game state is stored in a local SQLite database via SQLModel
- **Tier progression** — advance through tiers by completing missions and managing resources
- **Entropy system** — balance cycle generation against entropy buildup

---

## Setup

**Requirements:** Python 3.11+

### macOS / Linux

```bash
git clone https://github.com/Shonitbar/script-runner.git
cd script-runner
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Windows

```bash
git clone https://github.com/Shonitbar/script-runner.git
cd script-runner
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

`pip install -e .` installs all dependencies and registers the `scriptrunner` command.

---

## Running the Game

```bash
scriptrunner start
```

Starts both the API server (`http://localhost:8000`) and the TUI dashboard in one command.

> **Server only** (e.g. to run scripts while the TUI is open elsewhere):
> ```bash
> scriptrunner server
> ```

---

## Playing

A starter script is included to get you up and running immediately:

```bash
python player/starter.py
```

From there, write your own scripts to mine cycles, manage entropy, complete missions, and progress through tiers.

See the [Player Guide](player/player-guide.md) for the full API reference, mechanics, and mission walkthroughs.

---

## Tech Stack

| Layer | Library |
|-------|---------|
| API server | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Database | [SQLModel](https://sqlmodel.tiangolo.com/) (SQLite) |
| TUI | [Textual](https://textual.textualize.io/) + [Rich](https://rich.readthedocs.io/) |
| CLI | [Typer](https://typer.tiangolo.com/) |

---

<div align="center">

Made with Python · MIT License · [Open an issue](https://github.com/Shonitbar/script-runner/issues)

</div>
