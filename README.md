---
title: GhostCode
emoji: "👻"
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# GhostCode

> **An RL environment for autonomous debugging of legacy software systems.**  
> Built for the OpenEnv AI Hackathon — Meta × Hugging Face × PyTorch.

[![Hugging Face Space](https://img.shields.io/badge/🤗%20HF%20Space-Madhesh4124%2FGhostCode-blue)](https://huggingface.co/spaces/Madhesh4124/GhostCode)
[![OpenEnv Compliant](https://img.shields.io/badge/OpenEnv-0.1.0%20Compliant-green)](https://github.com/meta-pytorch/OpenEnv)
[![Average Score](https://img.shields.io/badge/Baseline%20Score-1.0%20%2F%201.0-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-3.11-blue)]()

---

## What is GhostCode?

GhostCode simulates a **broken legacy software system** that an AI agent must diagnose and repair. The agent navigates a deterministic in-memory mock filesystem, reads logs, installs packages, fixes configuration files, and patches source code — all through discrete tool-based actions.

It is designed as a **reinforcement learning environment** where agents learn to autonomously debug real-world failure patterns: missing dependencies, misconfigured environment variables, broken API routes, and syntax errors.

### Why is this useful for RL?

- **Real-world grounding** — the failure modes mirror actual production incidents
- **Structured action space** — discrete tools with clear preconditions and effects
- **Deterministic grading** — reproducible 0.0–1.0 scores, no randomness in evaluation
- **Progressive difficulty** — three tiers that stress-test different agent capabilities
- **Fast iteration** — no Docker sandbox, pure in-memory execution for speed

---

## Environment Design

### Tasks

| Task ID | Difficulty | Max Steps | Description |
|---|---|---|---|
| `easy_missing_dep` | Easy | 10 | Fix a missing pandas import in `app.py` |
| `medium_config_route` | Medium | 20 | Fix wrong `DB_PATH` in `.env` + broken API route in `app.py` |
| `hard_multi_failure` | Hard | 35 | Fix syntax error, missing packages, and multiple wrong env vars simultaneously |

All tasks are **seed-based** — passing `seed=42` always produces the same broken system, ensuring reproducibility across agent runs.

### Action Space

| Action | Parameters | Description |
|---|---|---|
| `read_file` | `path` | Read a file from the mock filesystem |
| `write_file` | `path`, `content` | Write/overwrite a file |
| `run_service` | — | Validate the current system state |
| `install_package` | `package` | Install a required dependency |
| `search_logs` | `keyword` | Search `logs.txt` for a keyword |
| `list_directory` | `path` | List files at a path |

### Observation Space

```json
{
  "terminal_output": "ERROR at line 6: NameError: name 'frame' is not defined",
  "file_contents": null,
  "file_tree": ["app.py", "logs.txt", "requirements.txt"],
  "current_path": "/"
}
```

### Reward Structure

| Event | Reward |
|---|---|
| Task complete (grade = 1.0) | +100 |
| First read of a required file | +10 |
| Each step taken | −1 |
| Invalid action | −5 |

### Grading

Each task has a deterministic grader that checks filesystem state:

- **Easy** — `pandas` installed (0.5) + `import pandas` in `app.py` (0.5)
- **Medium** — correct `DB_PATH` (0.33) + broken route removed (0.33) + valid Python syntax (0.34)
- **Hard** — packages installed (0.2) + env vars correct (0.2) + no syntax error (0.2) + correct imports (0.2) + `logs.txt` read (0.2)

---

## Baseline Results

Evaluated using a hybrid **rule-based + LLM agent** (Mistral Mamba Codestral 7B via NVIDIA API).  
The rule-based agent handles reads/installs; the LLM handles all `write_file` actions.

| Task | Score | Steps | LLM Calls |
|---|---|---|---|
| `easy_missing_dep` | **1.0** | 4 | 1 |
| `medium_config_route` | **1.0** | 7 | 3 |
| `hard_multi_failure` | **1.0** | 5 | 2 |
| **Average** | **1.0** | — | — |

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/Madhesh4124/GhostCode
cd GhostCode
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the server

```bash
python server.py
# Server starts at http://localhost:7860
```

### 3. Run baseline inference

```bash
# Rule-based agent only
python inference.py

# With LLM agent (requires NVIDIA API key)
API_KEY=your_nvidia_key python inference.py
```

---

## API Reference

Base URL: `https://Madhesh4124-ghostcode.hf.space`  
Interactive docs: [`/docs`](https://Madhesh4124-ghostcode.hf.space/docs)

### `GET /health`
```bash
curl https://Madhesh4124-ghostcode.hf.space/health
# {"status": "ok", "environment": "GhostCode"}
```

### `GET /info`
```bash
curl https://Madhesh4124-ghostcode.hf.space/info
# Returns environment metadata, task list, and available actions
```

### `POST /reset`
```bash
curl -X POST https://Madhesh4124-ghostcode.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_missing_dep", "seed": 42}'
# Returns session_id + initial observation
```

### `POST /step/{session_id}`
```bash
curl -X POST https://Madhesh4124-ghostcode.hf.space/step/{session_id} \
  -H "Content-Type: application/json" \
  -d '{"action_type": "read_file", "path": "logs.txt"}'
# Returns observation, reward, done, info
```

### `POST /close/{session_id}`
```bash
curl -X POST https://Madhesh4124-ghostcode.hf.space/close/{session_id}
# {"status": "closed"}
```

### WebSocket `/ws`
Real-time agent loop. Connect with query params `?task_id=easy_missing_dep&seed=42`.

```
Client → {"action_type": "read_file", "path": "logs.txt"}
Server → {"type": "step", "observation": {...}, "reward": 9, "done": false, "info": {...}}
```

---

## Project Structure

```
GhostCode/
├── env/
│   ├── environment.py     # GhostCodeEnv — reset, step, state, close
│   ├── filesystem.py      # MockFilesystem — in-memory file operations
│   ├── tasks.py           # Task definitions with seed-based randomization
│   └── graders.py         # Deterministic graders returning 0.0–1.0
├── models/
│   └── models.py          # ActionModel, ObservationModel, StateModel
├── server.py              # FastAPI server — REST + WebSocket endpoints
├── inference.py           # Baseline agent runner (rule-based + LLM)
├── test_env.py            # Environment unit tests
├── openenv.yaml           # OpenEnv spec declaration
├── Dockerfile             # HF Spaces Docker config
└── requirements.txt
```

---

## Running Tests

```bash
python test_env.py
# All three tasks should pass with score 1.0
```

---

## Design Decisions

**Mock filesystem over Docker sandbox** — chosen for reproducibility and speed in evaluation. Every run with the same seed produces the exact same broken system, making grading fully deterministic.

**Hybrid agent architecture** — the rule-based agent handles all deterministic steps (reads, installs); the LLM only fires on `write_file` actions where reasoning about file content is required. This minimises API calls while preserving LLM utility.

**Grade-gated early exit** — the task runner only exits early when the grader confirms score >= 1.0, not when `run_service` reports success. This ensures all grader checks are satisfied before termination.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `API_KEY` | — | NVIDIA API key for LLM agent |
| `MODEL_NAME` | `mistralai/mamba-codestral-7b-v0.1` | LLM model to use |
| `MAX_LLM_CALLS_PER_TASK` | `3` | LLM call budget per task |
| `PORT` | `7860` | Server port |

---

## Links

- 🤗 **HF Space**: [Madhesh4124/GhostCode](https://huggingface.co/spaces/Madhesh4124/GhostCode)
- 📦 **GitHub**: [Madhesh4124/GhostCode](https://github.com/Madhesh4124/GhostCode)
- 🏆 **Hackathon**: [OpenEnv AI Hackathon](https://pytorch.org/event/openenv-ai-hackathon/)
- 📖 **OpenEnv Spec**: [meta-pytorch/OpenEnv](https://github.com/meta-pytorch/OpenEnv)

---

## Author

**Madhesh** — built for India's first OpenEnv AI Hackathon (Meta × Hugging Face × PyTorch), Round 1, April 2026.
