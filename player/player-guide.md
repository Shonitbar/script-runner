# ScriptRunner — Player Guide

> A local-first, terminal-native idle/clicker game. You write scripts. The machine responds.

---

## Setup
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

---

## Resources

| Symbol | Name | What It Is |
|--------|------|------------|
| `⚙` | Cycles | Primary currency. Earned by mining. Gates tier progression. |
| `⚡` | Entropy | Pressure mechanic. Rises when you mine, decays at rest. Too high = locked out. |
| `◈` | Synth | Prestige token. Rare. Earned from specific missions only. |

---

## Entropy Risk Zones

This is the core mechanic. Entropy changes what mining earns and what it risks.

| Zone | Range | Mine Yield | Risk |
|------|-------|------------|------|
| Safe | `< 30` | +1 cycle | None |
| Caution | `30 – 70` | +2 cycles | None |
| Danger | `70 – 90` | +5 cycles | 10% chance to lose 50 cycles |
| Critical | `> 90` | Mining disabled | Must compress or wait |

**Entropy decay:** -0.1/sec while idle (no mining).
**Each mine call:** +0.5 entropy.

---

## API Reference

All endpoints are at `http://localhost:8000`.

| Method | Endpoint | Tier | Description |
|--------|----------|------|-------------|
| `GET` | `/status` | 0 | Current cycles, entropy, synth, tier |
| `POST` | `/mine` | 0 | Earn cycles. 1-second cooldown. 429 if too fast. |
| `GET` | `/status/history` | 0* | Last 20 API calls. Unlocks after First Contact. |
| `GET` | `/missions` | 1+ | List all missions as JSON. |
| `POST` | `/automate` | 2 | Register a named automation (+0.5 cycles/sec passive). |
| `GET` | `/automate` | 2 | List registered automations. |
| `POST` | `/compress` | 2 | Spend 100 cycles → reduce entropy by 20. |
| `POST` | `/pipeline` | 3 | Chain multiple ops in one request (mine/compress/status). |
| `POST` | `/overclock` | 3 | Double mine yield for 30s. Costs +30 entropy. |
| `POST` | `/exploit` | 3 | 50/50: +500 cycles or entropy +40. |
| `POST` | `/prestige` | — | Reset Protocol. Requires 5 Synth. |
| `GET` | `/prestige/status` | — | Check Synth count and prestige readiness. |
| `GET` | `/dark-ops/manifest` | Prestige | The classified mission brief. |
| `GET` | `/dark-ops/hint/{1-5}` | Prestige | Collect HMAC key shards. |
| `POST` | `/dark-ops/spoof` | Prestige | Fake a mine with a signed payload. |
| `POST` | `/dark-ops/inject` | Prestige | Inject a ghost automation. High risk. |
| `POST` | `/dark-ops/finalize` | Prestige | The secret final mission. |
| `WS` | `/ws` | — | WebSocket stream. Live game state + typed events. |

---

## Tier Progression

```
Tier 0 → Tier 1: immediate (after First Contact)
Tier 1 → Tier 2: 500 cycles
Tier 2 → Tier 3: 5,000 cycles
Tier 3 → Prestige: 5 Synth
```

---

## Tier 0 — Boot Sequence

**Goal:** Run your first script.

The game provides `starter.py`. Run it:
```bash
python starter.py
```

Expected response:
```json
{ "cycles": 1, "entropy": 0.5, "gained": 1, "message": "cycle registered", "zone": "safe" }
```

### Missions

**First Contact**
- Call `POST /mine` once.
- Reward: +10 cycles, unlocks `GET /status/history`.
- *This completes automatically on your first mine.*

---

## Tier 1 — Manual Labor (0 → 500 cycles)

You have access to `/mine`, `/status`, `/status/history`.

### Missions

**Ten in a Row**
- Mine 10 times total.
- Reward: +50 cycles.
- Script example:
```python
import requests, time

for _ in range(10):
    r = requests.post("http://localhost:8000/mine")
    print(r.json())
    time.sleep(1.1)  # respect the 1s cooldown
```

**The Watcher**
- Call `GET /status` 20 times and print entropy each time.
- Reward: +80 cycles.
```python
import requests, time

for _ in range(20):
    r = requests.get("http://localhost:8000/status")
    data = r.json()
    print(f"entropy: {data['entropy']}")
    time.sleep(0.5)
```

**Patience**
- Mine once, wait until entropy drops below 2.0, mine again.
- Reward: +120 cycles.
- *The mine raises entropy by 0.5. At rest it decays at 0.1/sec — so 5 seconds minimum.*
```python
import requests, time

requests.post("http://localhost:8000/mine")
print("waiting for entropy to drop...")

while True:
    r = requests.get("http://localhost:8000/status")
    e = r.json()["entropy"]
    print(f"entropy: {e}")
    if e < 2.0:
        break
    time.sleep(1)

r = requests.post("http://localhost:8000/mine")
print(r.json())
```

**Grinder** *(Tier unlock)*
- Accumulate 500 cycles total.
- Reward: Tier 2 unlocked + 1 free Synth.
- *Just keep mining. Loop with a 1.1s sleep to stay off the cooldown.*

---

## Tier 2 — Scripting (500 → 5,000 cycles)

New endpoints: `/automate`, `/missions`, `/compress`.

### Key mechanics

**Automations** — Register a named task. Server awards +0.5 cycles/sec passively while it's active.
```python
requests.post("http://localhost:8000/automate", json={"name": "my-bot", "interval_sec": 5})
```

**Compress** — Costs 100 cycles, reduces entropy by 20. Your pressure-relief valve.
```python
requests.post("http://localhost:8000/compress")
```

**Missions via API** — Fetch missions as JSON and script against them.
```python
import requests
missions = requests.get("http://localhost:8000/missions").json()
for m in missions:
    print(f"[{'X' if m['completed'] else ' '}] {m['name']} — {m['reward_cycles']}cy")
```

### Missions

**Loop Artist**
- Mine 50 times in a single script run.
- Reward: +300 cycles + 1 Synth.
- *Handle 429s — if you get one, `time.sleep(1.1)` and retry.*
```python
import requests, time

count = 0
while count < 50:
    r = requests.post("http://localhost:8000/mine")
    if r.status_code == 429:
        time.sleep(1.1)
        continue
    print(r.json())
    count += 1
    time.sleep(1.1)

print(f"Done — mined {count} times")
```

**The Compressor**
- Let entropy rise above 70, then compress it back below 30.
- Reward: +200 cycles.
- *Mine aggressively until entropy > 70, then call `/compress` multiple times.*
```python
import requests, time

# Mine until danger zone
while True:
    status = requests.get("http://localhost:8000/status").json()
    if status["entropy"] > 70:
        break
    requests.post("http://localhost:8000/mine")
    time.sleep(1.1)

print("Danger zone reached. Compressing...")

# Compress down below 30
while True:
    status = requests.get("http://localhost:8000/status").json()
    if status["entropy"] < 30:
        break
    if status["cycles"] >= 100:
        r = requests.post("http://localhost:8000/compress")
        print(r.json())
    else:
        time.sleep(5)  # wait for passive income or manual mines
```

**Mission Control**
- Write a script that fetches `/missions`, picks the highest-reward uncompleted one, and attempts it.
- Reward: +500 cycles + "AUTONOMOUS" badge on dashboard.
- *Design is up to you. The mechanic is that you're querying the game's own mission list to decide what to do.*

**Danger Zone**
- Mine 5 times while entropy > 70.
- Reward: +1 Synth if you survive, -200 cycles if you crash.
- *Risk/reward. Each danger-zone mine has a 10% chance to lose 50 cycles. Do it fast.*
```python
import requests, time

# First get entropy into danger zone
while True:
    status = requests.get("http://localhost:8000/status").json()
    if status["entropy"] >= 70:
        break
    requests.post("http://localhost:8000/mine")
    time.sleep(1.1)

print("In danger zone. Running 5 mines...")
for _ in range(5):
    r = requests.post("http://localhost:8000/mine")
    print(r.json())
    time.sleep(1.1)
```

**The Scheduler** *(Tier unlock preview)*
- Mine exactly once every 2 seconds for 60 seconds (±200ms tolerance).
- Reward: +400 cycles + unlocks `/overclock` preview.
- *The server measures intervals. Wrong interval = failed. Too long a gap (>5s) = reset. Wrong timing = disqualified.*
```python
import requests, time

print("Starting scheduler — 30 mines at 2s intervals...")
for i in range(30):
    r = requests.post("http://localhost:8000/mine")
    print(f"[{i+1}/30] {r.json()}")
    time.sleep(2.0)

print("Done!")
```

---

## Tier 3 — Systems (5,000 → 50,000 cycles)

New endpoints: `/pipeline`, `/overclock`, `/exploit`.

### Key mechanics

**Pipeline** — Chain up to 20 ops in one HTTP call. Ops: `mine`, `compress`, `status`.
```python
import requests

r = requests.post("http://localhost:8000/pipeline", json={
    "ops": [
        {"op": "mine"}, {"op": "mine"}, {"op": "mine"},
        {"op": "compress"},
        {"op": "mine"}, {"op": "mine"}, {"op": "mine"}
    ]
})
print(r.json())
```

**Volatility** — At Tier 3, entropy randomly spikes ±10 every 30–60 seconds. Build reactive scripts.

**WebSocket events** — Connect to `ws://localhost:8000/ws`. Listen for `entropy_spike` events.
```python
import asyncio, websockets, json

async def listen():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        async for msg in ws:
            data = json.loads(msg)
            print(data)

asyncio.run(listen())
```

### Missions

**Pipeline Engineer**
- Submit a `/pipeline` with: 3+ mines, 1+ compress, 3+ more mines (6 mines + 1 compress total).
- Reward: +2,000 cycles.
```python
import requests

r = requests.post("http://localhost:8000/pipeline", json={
    "ops": [
        {"op": "mine"}, {"op": "mine"}, {"op": "mine"},
        {"op": "compress"},
        {"op": "mine"}, {"op": "mine"}, {"op": "mine"}
    ]
})
print(r.json())
```

**The Listener**
- Connect to WebSocket. React to an `entropy_spike` event by calling `/compress` within 3 seconds.
- Reward: +1 Synth + "REACTIVE" badge.
```python
import asyncio, websockets, requests, json

async def listen():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        async for msg in ws:
            data = json.loads(msg)
            if data.get("type") == "entropy_spike":
                print("Spike detected! Compressing...")
                requests.post("http://localhost:8000/compress")
                break

asyncio.run(listen())
```

**Overclock Runner**
- Call `POST /overclock`, then mine as many times as possible in 30 seconds.
- Reward: +3,000 cycles if you get >25 mines in the window.
- *Overclock doubles yield but adds +30 entropy immediately. Mine as fast as the cooldown allows.*
```python
import requests, time

r = requests.post("http://localhost:8000/overclock")
print(r.json())

print("Mining hard for 30 seconds...")
start = time.time()
count = 0
while time.time() - start < 30:
    r = requests.post("http://localhost:8000/mine")
    if r.status_code != 429:
        count += 1
        print(f"[{count}] {r.json()}")
    time.sleep(1.05)

print(f"Total mines: {count}")
```

**Full Auto**
- Build a script that runs indefinitely:
  - Monitors `/status` every 5s
  - Mines when entropy < 60
  - Compresses when entropy > 75
  - Pauses when entropy > 90
- Run it unattended for 10 minutes.
- Reward: +5,000 cycles + 2 Synth.
```python
import requests, time

def run():
    while True:
        status = requests.get("http://localhost:8000/status").json()
        e = status["entropy"]
        c = status["cycles"]
        print(f"cycles={c:.1f} entropy={e:.1f}")

        if e > 90:
            print("Critical — pausing...")
            time.sleep(5)
        elif e > 75 and c >= 100:
            print("Compressing...")
            requests.post("http://localhost:8000/compress")
        elif e < 60:
            r = requests.post("http://localhost:8000/mine")
            if r.status_code != 429:
                print(f"Mined: {r.json()}")
            time.sleep(1.1)
            continue

        time.sleep(5)

run()
```

---

## Prestige — Reset Protocol

**Trigger:** Collect 5 Synth (`◈`), then call `POST /prestige`.

Check your status first:
```python
import requests
print(requests.get("http://localhost:8000/prestige/status").json())
```

When ready:
```python
import requests
r = requests.post("http://localhost:8000/prestige")
print(r.json())
```

### What resets
- Cycles → 0
- Tier → 0
- All missions reset

### What carries over
- **Cycle multiplier ×1.5** (stacks each prestige)
- **Dark Ops unlocked** — available from Tier 1 in all future runs

---

## Dark Ops (Prestige-Only)

Dark Ops is a puzzle layer. You need to collect 5 HMAC key shards, reconstruct a signing key, and submit a signed payload.

### Step 1 — Read the manifest
```python
import requests
r = requests.get("http://localhost:8000/dark-ops/manifest")
print(r.json()["manifest"])
```

### Step 2 — Collect 5 shards
```python
import requests

key = ""
for i in range(1, 6):
    r = requests.get(f"http://localhost:8000/dark-ops/hint/{i}")
    data = r.json()
    key += data["fragment"]
    print(f"Shard {i}: {data['fragment']} — collected {data['shards_collected']}/5")

print(f"Reconstructed key: {key}")
```

### Step 3 — Submit the final payload

Once you have all 5 shards and know the key, sign and submit:
```python
import requests, hmac, hashlib, json, time

key = b"<reconstructed_key>"  # fill in after collecting shards
ts = int(time.time())
agent = "your_name"

payload = {"timestamp": ts, "agent": agent}
payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
sig = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()

r = requests.post("http://localhost:8000/dark-ops/finalize", json={
    "timestamp": ts,
    "agent": agent,
    "signature": sig,
})
print(r.json())
```

> Timestamp must be within 5 minutes of submission. Don't generate it too early.

### Other Dark Ops endpoints

**Spoof** — Sign a `payload` dict with HMAC-SHA256 and get +200 cycles per success. Wrong signature = entropy +20.
```python
import requests, hmac, hashlib, json

key = b"<key>"
payload = {"action": "mine", "amount": 1}
payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
sig = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()

r = requests.post("http://localhost:8000/dark-ops/spoof", json={
    "payload": payload,
    "signature": sig,
})
print(r.json())
```

**Inject** — High-risk, high-reward. Three outcomes:
- 33%: Critical failure — entropy +50, -200 cycles
- 33%: Partial success — +100 cycles, entropy +15
- 33%: Full success — +400 cycles, ghost automation registered

```python
import requests
r = requests.post("http://localhost:8000/dark-ops/inject")
print(r.json())
```

---

## WebSocket Stream

Connect to `ws://localhost:8000/ws` for live game state. Pushes a `state` payload every second, plus typed events like `entropy_spike`.

Payload shape:
```json
{
  "type": "state",
  "cycles": 1234.5,
  "entropy": 42.0,
  "synth": 2,
  "tier": 2,
  "cycle_multiplier": 1.0,
  "overclock_active": false,
  "overclock_remaining": 0,
  "prestige_count": 0,
  "dark_ops_unlocked": false,
  "missions": [...],
  "logs": [...],
  "automations": [...]
}
```

---

## Quick Reference — Synth Sources

| Mission | Synth |
|---------|-------|
| Grinder (Tier 1 unlock) | 1 |
| Loop Artist | 1 |
| Danger Zone (survived) | 1 |
| The Listener | 1 |
| Full Auto | 2 |
| Dark Ops: Finalize | 10 |

**You need 5 Synth to prestige.** Plan accordingly.

---

## Tips for Testers

- **Entropy ≥ 90 = hard lock.** Call `/compress` or wait. Don't panic.
- **The 1-second mine cooldown** is enforced globally server-side. Parallel calls won't help.
- **Missions complete automatically** — no separate submission call needed. The server detects conditions on each API hit.
- **Pipeline cooldown is shared** with individual `/mine` calls. You can't bypass the 1s limit through pipelines.
- **The Scheduler mission resets** if you take a gap >5 seconds between mines, or fails permanently if your interval is wrong. Run it clean.
- **Prestige multiplier stacks** — each prestige multiplies your multiplier by 1.5 (1.0 → 1.5 → 2.25 → ...).
- **Dark Ops finalize has a 5-minute timestamp window** — generate your timestamp immediately before submitting.
