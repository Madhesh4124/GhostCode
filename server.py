# API Server for GhostCode module
import json
import os
import uuid
from dotenv import load_dotenv

load_dotenv()
import uvicorn

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from env.environment import GhostCodeEnv
from models.models import ActionModel

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="GhostCode OpenEnv Server", version="0.1.0")

# Module-level session store  {session_id: GhostCodeEnv}
_sessions: dict[str, GhostCodeEnv] = {}

# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task_id: str = "easy_missing_dep"
    seed: int = 42


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "ok", "environment": "GhostCode"}


@app.get("/info")
async def info():
    """Static metadata about the environment."""
    # Spin up a temporary env just to confirm it initialises cleanly.
    _tmp = GhostCodeEnv()
    return {
        "name": "ghostcode",
        "version": "0.1.0",
        "description": "RL environment for autonomous debugging",
        "tasks": [
            "easy_missing_dep",
            "medium_config_route",
            "hard_multi_failure",
        ],
        "actions": [
            "read_file",
            "write_file",
            "run_service",
            "install_package",
            "search_logs",
            "list_directory",
        ],
    }


@app.post("/reset")
async def reset_session(body: ResetRequest):
    """Create a new environment session and return the initial observation."""
    env = GhostCodeEnv(verbose=False)
    obs = env.reset(task_id=body.task_id, seed=body.seed)

    session_id = str(uuid.uuid4())
    _sessions[session_id] = env

    return {
        "session_id": session_id,
        "observation": obs.model_dump(),
    }


@app.post("/step/{session_id}")
async def step_session(session_id: str, action: ActionModel):
    """Advance an existing session by one action."""
    env = _sessions.get(session_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    obs, reward, done, info = env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.post("/close/{session_id}")
async def close_session(session_id: str):
    """Close and remove an environment session."""
    env = _sessions.pop(session_id, None)
    if env is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    env.close() if hasattr(env, "close") else None
    return {"status": "closed"}


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    task_id: str = "easy_missing_dep",
    seed: int = 42,
):
    """
    Real-time agent ↔ environment loop over WebSocket.

    Query params:
        task_id  – which task to run (default: easy_missing_dep)
        seed     – random seed for task generation (default: 42)

    Protocol (newline-delimited JSON):
        Server → Client on connect:
            {"type": "reset", "observation": {...}, "task_id": "..."}

        Client → Server each step:
            {"action_type": "read_file", "path": "app.py", ...}

        Server → Client each step:
            {"type": "step", "observation": {...}, "reward": -1.0, "done": false, "info": {...}}

        Server → Client when done:
            {"type": "done", "final_score": 1.0, "steps": 10}
            <connection closed>

        Server → Client on bad action:
            {"type": "error", "message": "Invalid action format"}
            <connection stays open — agent may retry>
    """
    await websocket.accept()

    env = GhostCodeEnv(verbose=False)

    try:
        # ---- Reset and send initial observation ----
        obs = env.reset(task_id=task_id, seed=seed)
        await websocket.send_text(
            json.dumps({
                "type": "reset",
                "observation": obs.model_dump(),
                "task_id": task_id,
            })
        )

        # ---- Agent loop ----
        async for raw_message in websocket.iter_text():
            # Parse action
            try:
                data = json.loads(raw_message)
                action = ActionModel(**data)
            except Exception:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid action format"})
                )
                continue  # Let the agent retry

            # Execute step
            obs, reward, done, info = env.step(action)

            await websocket.send_text(
                json.dumps({
                    "type": "step",
                    "observation": obs.model_dump(),
                    "reward": reward,
                    "done": done,
                    "info": info,
                })
            )

            # Episode finished
            if done:
                await websocket.send_text(
                    json.dumps({
                        "type": "done",
                        "final_score": info.get("grade", 0.0),
                        "steps": info.get("steps", env._state.step_count if env._state else 0),
                    })
                )
                await websocket.close()
                break

    except WebSocketDisconnect:
        pass  # Normal client disconnect
    finally:
        if hasattr(env, "close"):
            env.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
