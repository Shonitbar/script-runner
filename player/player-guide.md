# ScriptRunner — Player Guide

> A local-first, terminal-native idle/clicker game. You write scripts. The machine responds.

---

## Setup
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

## Running the Game

```bash
scriptrunner start
```

This starts both the server (`http://localhost:8000`) and the TUI dashboard in one command.

> If you want a server-only instance (e.g. to run scripts while the TUI is open elsewhere), use `scriptrunner server`.

---

## A Note on HTTP Sessions

All examples use `requests.Session()` rather than bare `requests.get/post`. Sessions reuse the underlying TCP connection — faster round-trips, fewer dropped calls, especially during tight mining loops.

```python
import requests
session = requests.Session()
# use session.get(...) and session.post(...) throughout
```

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
Tier 0 → Tier 1:  immediate (after First Contact)
Tier 1 → Tier 2:  complete Grinder (500 cycles total)
Tier 2 → Tier 3:  complete Scaler (5,000 cycles total)
Tier 3 → Prestige: complete Titan (50,000 cycles) → earn 5 Synth → call /prestige
```

---

## Tier 0 — Boot Sequence

**Goal:** Run your first script.

The game provides `starter.py`. Run it:
```bash
python player/starter.py
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
```python
import requests, time

session = requests.Session()
for _ in range(10):
    r = session.post("http://localhost:8000/mine")
    print(r.json())
    time.sleep(1.1)  # respect the 1s cooldown
```

**The Watcher**
- Call `GET /status` 20 times and print entropy each time.
- Reward: +80 cycles.
```python
import requests, time

session = requests.Session()
for _ in range(20):
    r = session.get("http://localhost:8000/status")
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

session = requests.Session()
session.post("http://localhost:8000/mine")
print("waiting for entropy to drop...")

while True:
    r = session.get("http://localhost:8000/status")
    e = r.json()["entropy"]
    print(f"entropy: {e}")
    if e < 2.0:
        break
    time.sleep(1)

r = session.post("http://localhost:8000/mine")
print(r.json())
```

**Grinder** *(Tier unlock)*
- Accumulate 500 cycles total.
- Reward: Tier 2 unlocked + 1 Synth.
- *Just keep mining. Loop with a 1.1s sleep to stay off the cooldown.*

---

## Tier 2 — Scripting (500 → 5,000 cycles)

New endpoints: `/automate`, `/missions`, `/compress`.

### Key mechanics

**Automations** — Register a named task. Server awards +0.5 cycles/sec passively while it's active.
```python
import requests

session = requests.Session()
session.post("http://localhost:8000/automate", json={"name": "my-bot", "interval_sec": 5})
```

**Compress** — Costs 100 cycles, reduces entropy by 20. Your pressure-relief valve.
```python
import requests

session = requests.Session()
session.post("http://localhost:8000/compress")
```

**Missions via API** — Fetch missions as JSON and script against them.
```python
import requests

session = requests.Session()
missions = session.get("http://localhost:8000/missions").json()
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

session = requests.Session()
count = 0
while count < 50:
    r = session.post("http://localhost:8000/mine")
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

session = requests.Session()

# Mine until danger zone
while True:
    status = session.get("http://localhost:8000/status").json()
    if status["entropy"] > 70:
        break
    session.post("http://localhost:8000/mine")
    time.sleep(1.1)

print("Danger zone reached. Compressing...")

# Compress down below 30
while True:
    status = session.get("http://localhost:8000/status").json()
    if status["entropy"] < 30:
        break
    if status["cycles"] >= 100:
        r = session.post("http://localhost:8000/compress")
        print(r.json())
    else:
        time.sleep(5)
```

**Danger Zone**
- Mine 5 times while entropy > 70.
- Reward: +1 Synth if you survive, -200 cycles if you crash.
- *Risk/reward. Each danger-zone mine has a 10% chance to lose 50 cycles. Do it fast.*
```python
import requests, time

session = requests.Session()

# Get entropy into danger zone first
while True:
    status = session.get("http://localhost:8000/status").json()
    if status["entropy"] >= 70:
        break
    session.post("http://localhost:8000/mine")
    time.sleep(1.1)

print("In danger zone. Running 5 mines...")
for _ in range(5):
    r = session.post("http://localhost:8000/mine")
    print(r.json())
    time.sleep(1.1)
```

**The Scheduler** *(Tier unlock preview)*
- Mine exactly once every 2 seconds for 60 seconds (±200ms tolerance).
- Reward: +400 cycles.
- *The server measures intervals. Wrong interval = failed. Too long a gap (>5s) = reset.*
```python
import requests, time

session = requests.Session()
print("Starting scheduler — 30 mines at 2s intervals...")
for i in range(30):
    r = session.post("http://localhost:8000/mine")
    print(f"[{i+1}/30] {r.json()}")
    time.sleep(2.0)

print("Done!")
```

**Scaler** *(Tier unlock)*
- Accumulate 5,000 cycles total.
- Reward: Tier 3 unlocked + 1 Synth.
- *Keep your loop running. Compress when entropy climbs to stay in the higher-yield zones.*
```python
import requests, time

session = requests.Session()
while True:
    status = session.get("http://localhost:8000/status").json()
    print(f"cycles={status['cycles']:.0f} entropy={status['entropy']:.1f}")
    if status["entropy"] > 75 and status["cycles"] >= 100:
        session.post("http://localhost:8000/compress")
    elif status["entropy"] < 90:
        session.post("http://localhost:8000/mine")
    time.sleep(1.1)
```

---

## Tier 3 — Systems (5,000 → 50,000 cycles)

New endpoints: `/pipeline`, `/overclock`, `/exploit`.

### Key mechanics

**Pipeline** — Chain up to 20 ops in one HTTP call. Ops: `mine`, `compress`, `status`.
```python
import requests

session = requests.Session()
r = session.post("http://localhost:8000/pipeline", json={
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

session = requests.Session()
r = session.post("http://localhost:8000/pipeline", json={
    "ops": [
        {"op": "mine"}, {"op": "mine"}, {"op": "mine"},
        {"op": "compress"},
        {"op": "mine"}, {"op": "mine"}, {"op": "mine"}
    ]
})
print(r.json())
```

**Overclock Runner**
- Call `POST /overclock`, then mine as many times as possible in 30 seconds.
- Reward: +3,000 cycles if you get >25 mines in the window.
- *Overclock doubles yield but adds +30 entropy immediately. Mine as fast as the cooldown allows.*
```python
import requests, time

session = requests.Session()
r = session.post("http://localhost:8000/overclock")
print(r.json())

print("Mining hard for 30 seconds...")
start = time.time()
count = 0
while time.time() - start < 30:
    r = session.post("http://localhost:8000/mine")
    if r.status_code != 429:
        count += 1
        print(f"[{count}] {r.json()}")
    time.sleep(1.05)

print(f"Total mines: {count}")
```

**Full Auto**
- Register an automation via `POST /automate` and keep it running for 10 minutes (600 passive ticks).
- Reward: +5,000 cycles + 2 Synth.
- *The server counts passive ticks from active automations — one per second per registered bot. You don't need to babysit it, just make sure the server stays up.*
```python
import requests, time

session = requests.Session()

# Register the automation
r = session.post("http://localhost:8000/automate", json={"name": "full-auto", "interval_sec": 1})
print(r.json())

print("Automation registered. Running for 10 minutes...")
start = time.time()
while time.time() - start < 620:
    status = session.get("http://localhost:8000/status").json()
    print(f"cycles={status['cycles']:.0f} entropy={status['entropy']:.1f}")
    time.sleep(30)

print("Done — check mission completion.")
```

**Titan** *(Prestige unlock)*
- Accumulate 50,000 cycles total.
- Reward: 5 Synth — enough to trigger prestige.
- *This is the long grind. Use automations, pipelines, and overclock windows together.*
```python
import requests, time

session = requests.Session()
while True:
    status = session.get("http://localhost:8000/status").json()
    cycles = status["cycles"]
    entropy = status["entropy"]
    print(f"cycles={cycles:.0f}/50000 entropy={entropy:.1f}")

    if entropy >= 90:
        time.sleep(5)
    elif entropy > 75 and cycles >= 100:
        session.post("http://localhost:8000/compress")
    else:
        r = session.post("http://localhost:8000/mine")
        if r.status_code != 429:
            print(r.json())
    time.sleep(1.1)
```

---

## Prestige — Reset Protocol

**Trigger:** Complete Titan to earn 5 Synth (`◈`), then call `POST /prestige`.

Check your status first:
```python
import requests

session = requests.Session()
print(session.get("http://localhost:8000/prestige/status").json())
```

When ready:
```python
import requests

session = requests.Session()
r = session.post("http://localhost:8000/prestige")
print(r.json())
```

### What resets
- Cycles → 0
- Tier → 0
- All missions reset
- ENTITY companion resets (new DNA on your next 8 calls)

### What carries over
- **Cycle multiplier ×1.5** (stacks each prestige)
- **Dark Ops unlocked** — available from Tier 1 in all future runs

---

## Dark Ops (Prestige-Only)

Dark Ops is a puzzle layer. You need to collect 5 HMAC key shards, reconstruct a signing key, and submit a signed payload.

### Step 1 — Read the manifest
```python
import requests

session = requests.Session()
r = session.get("http://localhost:8000/dark-ops/manifest")
print(r.json()["manifest"])
```

### Step 2 — Collect 5 shards
```python
import requests

session = requests.Session()
key = ""
for i in range(1, 6):
    r = session.get(f"http://localhost:8000/dark-ops/hint/{i}")
    data = r.json()
    key += data["fragment"]
    print(f"Shard {i}: {data['fragment']} — collected {data['shards_collected']}/5")

print(f"Reconstructed key: {key}")
```

### Step 3 — Submit the final payload

Once you have all 5 shards and know the key, sign and submit:
```python
import requests, hmac, hashlib, json, time

session = requests.Session()
key = b"<reconstructed_key>"  # fill in after collecting shards
ts = int(time.time())
agent = "your_name"

payload = {"timestamp": ts, "agent": agent}
payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
sig = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()

r = session.post("http://localhost:8000/dark-ops/finalize", json={
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

session = requests.Session()
key = b"<key>"
payload = {"action": "mine", "amount": 1}
payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
sig = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()

r = session.post("http://localhost:8000/dark-ops/spoof", json={
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

session = requests.Session()
r = session.post("http://localhost:8000/dark-ops/inject")
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
  "automations": [...],
  "blob": {
    "total_requests": 120,
    "endpoints_seen": ["/mine", "/status", "/compress"],
    "dna_seed": 849302174
  }
}
```

---

## ENTITY — Your Companion

The TUI panel labelled **ENTITY** is a virtual companion that evolves silently as you play. You don't interact with it directly — it watches your API activity and grows.

### Evolution stages

| Stage | Calls needed | Name |
|-------|-------------|------|
| 1 | 0+ | dormant |
| 2 | 51+ | stirring |
| 3 | 201+ | awakening |
| 4 | 501+ | evolving |
| 5 | 2001+ | ascendant |

### DNA

After your first 8 API calls, the ENTITY locks in a **DNA seed** derived from the exact sequence of endpoints you hit. This seed permanently determines its eyes, mouth, limbs, aura shape, and color for the rest of the run. Two players who mine in different orders will have visually different entities.

The DNA seed is shown in the panel footer as a 6-character hex string. It never changes — until you prestige.

### Endpoint-driven features

Each endpoint you use for the first time unlocks a new body part:

| Endpoint first called | Feature unlocked |
|-----------------------|-----------------|
| `/mine` | Eyes appear |
| `/status` | Mouth appears |
| `/compress` | Arms appear |
| `/automate` | Body appears |
| `/overclock` | Eyes glow (◉) |
| `/pipeline` | Limb style changes |
| `/prestige` | Accent mark (∧) above head |
| any `/dark-ops/` | Heavy dark aura |

### Entropy aura

The aura surrounding the ENTITY reflects your current entropy level in real time — lighter at low entropy, heavier and denser as you push into danger zones.

### Prestige reset

When you prestige, the ENTITY resets completely. Your next run starts a fresh entity shaped by your new sequence of first 8 calls.

---

## Quick Reference — Synth Sources

| Mission | Synth |
|---------|-------|
| Grinder (Tier 1 unlock) | 1 |
| Loop Artist | 1 |
| Danger Zone (survived) | 1 |
| Scaler (Tier 2 unlock) | 1 |
| Full Auto | 2 |
| Titan | 5 |
| Dark Ops: Finalize | 10 |

**You need 5 Synth to prestige.** The fastest path: Grinder + Loop Artist + Danger Zone + Scaler = 4, then Full Auto puts you over.

---

## Tips for Testers

- **Entropy ≥ 90 = hard lock.** Call `/compress` or wait. Don't panic.
- **The 1-second mine cooldown** is enforced globally server-side. Parallel calls won't help — use `Session()` for speed, not concurrency.
- **Missions complete automatically** — no separate submission call needed. The server detects conditions on each API hit.
- **Pipeline cooldown is shared** with individual `/mine` calls. You can't bypass the 1s limit through pipelines.
- **The Scheduler mission resets** if you take a gap >5 seconds between mines, or fails permanently if your interval is wrong. Run it clean.
- **Full Auto tracks passive ticks**, not script runtime — register an automation and leave the server running for 10 minutes.
- **Prestige multiplier stacks** — each prestige multiplies your multiplier by 1.5 (1.0 → 1.5 → 2.25 → ...).
- **Dark Ops finalize has a 5-minute timestamp window** — generate your timestamp immediately before submitting.
- **ENTITY DNA is permanent per run** — your first 8 endpoints define it. Experiment across prestiges to see different forms.
