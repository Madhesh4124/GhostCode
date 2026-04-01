---
title: GhostCode
emoji: "👻"
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# GhostCode

> A reinforcement learning environment for autonomous debugging
> of legacy software systems.

---

## Problem Statement

Legacy codebases are notoriously fragile — poorly documented, filled with implicit dependencies, and prone to cascading failures that are difficult to trace. Current AI models excel at generating code in isolation, but lack the ability to interactively diagnose and repair a running system under realistic constraints. GhostCode fills this gap by providing a fully sandboxed, deterministic RL environment where agents must read logs, install packages, fix configuration, and rewrite broken code to restore a system to a working state.

---

## Environment Overview

- **Mock filesystem** — fully in-memory, deterministic, seeded per task
- **Discrete tool-based action space** — 6 actions that mirror real debugging workflows
- **3 tasks of increasing difficulty** — easy, medium, and hard
- **WebSocket API** — for real-time, bidirectional agent interaction
- **REST API** — for session-based step-by-step control

---

## Action Space

| Action | Parameters | Description |
|---|---|---|
| `read_file` | `path` | Read the contents of a file |
| `write_file` | `path`, `content` | Write or overwrite a file |
| `run_service` | — | Attempt to start the service and observe output |
| `install_package` | `package` | Install a Python package into the mock environment |
| `search_logs` | `keyword` | Search `logs.txt` for a specific keyword |
| `list_directory` | `path` | List files in a directory |

---

## Observation Space

| Field | Type | Description |
|---|---|---|
| `terminal_output` | `string` | Output from the last action or service run |
| `file_contents` | `string \| null` | Contents of the last file read (null otherwise) |
| `file_tree` | `string[]` | List of files in the current directory |
| `current_path` | `string` | Current working directory path |

---

## Tasks

| Task ID | Difficulty | Bug Type | Max Steps |
|---|---|---|---|
| `easy_missing_dep` | Easy | Missing `pandas` import and installation | 10 |
| `medium_config_route` | Medium | Broken DB path in `.env` and misconfigured API route | 20 |
| `hard_multi_failure` | Hard | Syntax error + missing packages + incorrect env vars | 35 |

---

## Reward Function

| Event | Reward |
|---|---|
| Terminal success (score ≥ 1.0) | `+100` |
| Step penalty (every step) | `−1` |
| Invalid / errored action | `−5` |
| First read of a required file (milestone) | `+10` |

---

## Grader

Each task returns a score from `0.0` to `1.0` based on weighted sub-checks.

| Task | Sub-checks |
|---|---|
| `easy_missing_dep` | `pandas` installed (0.5) · `import pandas` present in `app.py` (0.5) |
| `medium_config_route` | `DB_PATH=/app/db.sqlite` in env vars (0.33) · broken route removed from `app.py` (0.33) · `app.py` is valid Python (0.34) |
| `hard_multi_failure` | All packages installed (0.2) · all env vars corrected (0.2) · `app.py` syntax valid (0.2) · correct imports in `app.py` (0.2) · `logs.txt` read (0.2) |

---

## Project Structure

```
GhostCode/
├── server.py            # FastAPI + WebSocket server (OpenEnv API)
├── inference.py         # Baseline agent runner (rule-based + LLM)
├── openenv.yaml         # OpenEnv environment manifest
├── Dockerfile           # Container build definition
├── requirements.txt     # Python dependencies
├── test_env.py          # Environment unit tests
│
├── env/
│   ├── environment.py   # GhostCodeEnv — core reset/step/grade loop
│   ├── filesystem.py    # MockFilesystem — in-memory file + package state
│   ├── tasks.py         # Task factories (easy / medium / hard)
│   ├── graders.py       # Grading functions per task
│   └── __init__.py
│
└── models/
    ├── models.py        # Pydantic models: ActionModel, ObservationModel, StateModel
    └── __init__.py
```

---

## Setup & Running Locally

```bash
git clone https://github.com/Madhesh4124/GhostCode
cd GhostCode
pip install -r requirements.txt
python server.py
```

Server starts at `http://localhost:8000`.

---

## Running with Docker

```bash
docker build -t ghostcode .

docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  ghostcode
```

---

## Running Inference

```bash
# With LLM agent (needs API key)
export GEMINI_API_KEY=your_key
python inference.py

# Without API key (rule-based agent)
python inference.py
```

  

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe — returns `{"status": "ok"}` |
| `GET` | `/info` | Environment metadata (tasks, actions, version) |
| `WS` | `/ws?task_id=&seed=` | WebSocket agent connection — real-time loop |
| `POST` | `/reset` | Start a new episode, returns `session_id` + initial observation |
| `POST` | `/step/{session_id}` | Take one action, returns observation + reward + done |
| `POST` | `/close/{session_id}` | End episode and release session |

### WebSocket Message Flow

```
Client connects → Server sends {"type": "reset", "observation": {...}, "task_id": "..."}
Client sends    → {"action_type": "read_file", "path": "logs.txt"}
Server replies  → {"type": "step", "observation": {...}, "reward": 9, "done": false, "info": {...}}
...
Server sends    → {"type": "done", "final_score": 1.0, "steps": 7}
```

---

## Baseline Results

| Task | Agent | Score | Steps |
|---|---|---|---|
| `easy_missing_dep` | rule-based | TBD | TBD |
| `medium_config_route` | rule-based | TBD | TBD |
| `hard_multi_failure` | rule-based | TBD | TBD |

---

## Deployment

Hosted on Hugging Face Spaces:
[https://huggingface.co/spaces/Madhesh4124/GhostCode](https://huggingface.co/spaces/Madhesh4124/GhostCode)

Built with **FastAPI + WebSockets**. No external RL framework required.
