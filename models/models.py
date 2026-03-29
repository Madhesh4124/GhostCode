# Inference model interface and implementation
from typing import Optional, Literal
from pydantic import BaseModel, Field

class ObservationModel(BaseModel):
    """
    Represents what the agent sees at each step in the GhostCode environment.
    """
    terminal_output: str
    file_contents: Optional[str] = None  # Last file read, if any
    file_tree: list[str] = Field(default_factory=list)  # Current directory listing
    current_path: str

class ActionModel(BaseModel):
    """
    Represents a single action taken by the agent.
    """
    action_type: Literal[
        "read_file", 
        "write_file", 
        "run_service", 
        "install_package", 
        "search_logs", 
        "list_directory"
    ]
    path: Optional[str] = None
    content: Optional[str] = None
    package: Optional[str] = None
    keyword: Optional[str] = None

class StateModel(BaseModel):
    """
    Represents the full internal environment state of GhostCode.
    """
    filesystem: dict[str, str] = Field(default_factory=dict)  # filepath -> file content
    installed_packages: list[str] = Field(default_factory=list)
    env_vars: dict[str, str] = Field(default_factory=dict)
    step_count: int
    max_steps: int
    task_id: str
    done: bool
    required_reads: list[str] = Field(default_factory=list)     # Files agent must read for +10 reward
    files_read: list[str] = Field(default_factory=list)        # Files agent has already read
    required_packages: list[str] = Field(default_factory=list) # Packages required for the task
    required_env_vars: dict[str, str] = Field(default_factory=dict) # Env vars with expected values
