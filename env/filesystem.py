# Sandbox filesystem interaction logic
import ast
from typing import Optional

class MockFilesystem:
    """
    An in-memory Linux-like file system simulation for the GhostCode environment.
    """
    def __init__(self):
        self.files: dict[str, str] = {}
        self.installed_packages: list[str] = []
        self.env_vars: dict[str, str] = {}
        self.required_packages: list[str] = []
        self.required_env_vars: dict[str, str] = {}

    def reset(self, initial_files: dict[str, str], installed_packages: list[str], 
              env_vars: dict[str, str], required_packages: list[str], 
              required_env_vars: dict[str, str]):
        """
        Resets the file system and environment to specified initial values.
        """
        self.files = initial_files.copy()
        self.installed_packages = list(installed_packages)
        self.env_vars = env_vars.copy()
        self.required_packages = list(required_packages)
        self.required_env_vars = required_env_vars.copy()

    def read_file(self, path: str) -> str:
        """
        Returns file content or an error message if the file is not found.
        """
        if path in self.files:
            return self.files[path]
        return f"ERROR: File not found: {path}"

    def write_file(self, path: str, content: str) -> str:
        """
        Writes content to the specified path.
        """
        self.files[path] = content
        return f"SUCCESS: Written to {path}"

    def list_directory(self, path: str) -> list[str]:
        """
        Returns a list of file paths that exist under the given directory path.
        """
        if path == "/":
            return list(self.files.keys())
        # Normalize the path for directory listing (add trailing slash if missing)
        dir_path = path if path.endswith('/') else path + '/'
        return [f for f in self.files.keys() if f.startswith(dir_path) or f == path]

    def search_logs(self, keyword: str) -> str:
        """
        Searches 'logs.txt' for lines containing the keyword.
        """
        log_content = self.files.get("logs.txt", "")
        if not log_content:
            return f"No matches found for: {keyword}"

        matches = [line for line in log_content.splitlines() if keyword in line]
        if matches:
            return "\n".join(matches)
        return f"No matches found for: {keyword}"

    def install_package(self, package: str) -> str:
        """
        Adds a package to the list of installed packages.
        """
        if package not in self.installed_packages:
            self.installed_packages.append(package)
        return f"SUCCESS: Installed {package}"

    def run_service(self) -> str:
        """
        Validates the current filesystem state against requirements.
        Returns a success message or a list of configuration/syntax/dependency errors.
        """
        errors = []
        app_content = self.files.get("app.py", "")

        # 1. Dependency checks: check if all required packages are installed
        for pkg in self.required_packages:
            if pkg not in self.installed_packages:
                errors.append(f"ModuleNotFoundError: No module named '{pkg}'")

        # 2. Import checks in app.py: check if all required packages are imported
        for pkg in self.required_packages:
            if f"import {pkg}" not in app_content:
                errors.append(f"NameError: '{pkg}' is used but not imported in app.py")

        # 3. Syntax check: check if app.py has valid Python syntax
        try:
            if app_content:
                ast.parse(app_content)
        except SyntaxError as e:
            errors.append(f"SyntaxError in app.py: {str(e)}")

        # 4. Environment variable checks: check if all required ENV vars are present and correct
        for key, expected_value in self.required_env_vars.items():
            actual_value = self.env_vars.get(key)
            if actual_value != expected_value:
                errors.append(f"ConfigError: {key} is incorrect (got '{actual_value}')")

        if errors:
            return "Service failed to start:\n" + "\n".join(f"  - {e}" for e in errors)
        else:
            return "Service started successfully. All checks passed."
