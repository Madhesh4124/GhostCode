# GhostCode core environment logic
from typing import Tuple, Dict, Any, Optional
from models.models import ObservationModel, ActionModel, StateModel
from env.filesystem import MockFilesystem
from env.tasks import get_task
from env.graders import grade


class GhostCodeEnv:
    """
    The core OpenEnv environment for GhostCode, managing the lifecycle of an agent's task.
    """

    def __init__(self, verbose: bool = False):
        self.fs = MockFilesystem()
        self.verbose = verbose
        self.task_id = ""
        self._state: Optional[StateModel] = None
        self._task: Optional[Dict[str, Any]] = None
        self.last_render = ""

    def reset(
        self, task_id: str = "easy_missing_dep", seed: int = 42
    ) -> ObservationModel:
        """
        Loads a task and initializes the environment state.
        """
        self.task_id = task_id
        self._task = get_task(task_id, seed)

        # Parse initial env vars from the task files if present
        env_content = self._task["initial_files"].get(".env", "")
        initial_env_vars = self._parse_env(env_content)

        self.fs.reset(
            initial_files=self._task["initial_files"],
            installed_packages=[],
            env_vars=initial_env_vars,
            required_packages=self._task["required_packages"],
            required_env_vars=self._task["required_env_vars"],
        )

        self._state = StateModel(
            filesystem=self.fs.files,
            installed_packages=[],
            env_vars=self.fs.env_vars,
            step_count=0,
            max_steps=self._task["max_steps"],
            task_id=task_id,
            done=False,
            required_reads=self._task["required_reads"],
            files_read=[],
            required_packages=self._task["required_packages"],
            required_env_vars=self._task["required_env_vars"],
        )

        return ObservationModel(
            terminal_output=self.fs.read_file("logs.txt"),
            file_contents=None,
            file_tree=self.fs.list_directory("/"),
            current_path="/",
        )

    def _parse_env(self, content: str) -> Dict[str, str]:
        """Helper to parse .env file content into a dictionary."""
        env = {}
        for line in content.splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip()
        return env

    def step(
        self, action: ActionModel
    ) -> Tuple[ObservationModel, float, bool, Dict[str, Any]]:
        """
        Executes an action, updates the state, and returns the observation, reward, and status.
        """
        reward = -1.0  # Step penalty
        result = ""

        # Execute action via filesystem
        try:
            if action.action_type == "read_file":
                if not action.path:
                    result = "ERROR: No path provided for read_file"
                else:
                    result = self.fs.read_file(action.path)
                    if action.path in self.fs.files:
                        # Reward for reading required files for the first time
                        if (
                            action.path in self._state.required_reads
                            and action.path not in self._state.files_read
                        ):
                            reward += 10.0
                        if action.path not in self._state.files_read:
                            self._state.files_read.append(action.path)

            elif action.action_type == "write_file":
                if not action.path:
                    result = "ERROR: No path provided for write_file"
                else:
                    result = self.fs.write_file(action.path, action.content or "")
                    # Sync env_vars if .env is written
                    if action.path == ".env":
                        self.fs.env_vars = self._parse_env(action.content or "")

            elif action.action_type == "list_directory":
                result = str(self.fs.list_directory(action.path or "/"))

            elif action.action_type == "install_package":
                if not action.package:
                    result = "ERROR: No package provided for install_package"
                else:
                    result = self.fs.install_package(action.package)

            elif action.action_type == "search_logs":
                if not action.keyword:
                    result = "ERROR: No keyword provided for search_logs"
                else:
                    result = self.fs.search_logs(action.keyword)

            elif action.action_type == "run_service":
                result = self.fs.run_service()
            else:
                result = f"ERROR: Unknown action type: {action.action_type}"

        except Exception as e:
            result = f"ERROR: Internal error: {str(e)}"

        if result.startswith("ERROR"):
            reward -= 5.0

        # Update environment state
        self._state.step_count += 1
        self._state.filesystem = self.fs.files
        self._state.installed_packages = self.fs.installed_packages
        self._state.env_vars = self.fs.env_vars

        # Grading and Termination
        current_grade = grade(self.task_id, self._state)
        if current_grade >= 1.0:
            reward += 100.0
            self._state.done = True

        if self._state.step_count >= self._state.max_steps:
            self._state.done = True

        # Create Observation
        obs = ObservationModel(
            terminal_output=result,
            file_contents=result
            if action.action_type == "read_file" and not result.startswith("ERROR")
            else None,
            file_tree=self.fs.list_directory("/"),
            current_path="/",
        )

        # Rendering
        self.last_render = self.render_step(
            self._state.step_count, action, result, reward
        )
        if self.verbose:
            print(self.last_render)

        return obs, reward, self._state.done, {"grade": current_grade}

    def state(self) -> StateModel:
        """Returns the current internal environment state."""
        return self._state

    def render_step(
        self, step_num: int, action: ActionModel, result: str, reward: float
    ) -> str:
        """Formats a step summary for logging/visualization."""
        params = []
        if action.path:
            params.append(f"path='{action.path}'")
        if action.package:
            params.append(f"pkg='{action.package}'")
        if action.keyword:
            params.append(f"key='{action.keyword}'")
        param_str = ", ".join(params)

        # Format result to be single-line and truncated
        res_summary = result.replace("\n", " ")
        if len(res_summary) > 120:
            res_summary = res_summary[:117] + "..."

        border = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return (
            f"\n{border}\n"
            f"Task: {self.task_id}  |  Step {step_num}\n"
            f"{border}\n"
            f"Action  : {action.action_type}({param_str})\n"
            f"Result  : {res_summary}\n"
            f"Reward  : {reward:+.0f}\n"
            f"{border}\n"
        )
