# Task grading and evaluation logic
import ast
from models.models import StateModel

def grade_easy(state: StateModel) -> float:
    """
    Grades the easy task: pandas installation and import.
    """
    score = 0.0
    # Check 1 (0.5): "pandas" is in state.installed_packages
    if "pandas" in state.installed_packages:
        score += 0.5
    
    # Check 2 (0.5): state.filesystem["app.py"] contains "import pandas"
    app_content = state.filesystem.get("app.py", "")
    if "import pandas" in app_content:
        score += 0.5
        
    return round(score, 2)

def grade_medium(state: StateModel) -> float:
    """
    Grades the medium task: DB_PATH config and route fix.
    """
    score = 0.0
    # Check 1 (0.33): state.env_vars["DB_PATH"] == "/app/db.sqlite"
    if state.env_vars.get("DB_PATH") == "/app/db.sqlite":
        score += 0.33
        
    # Check 2 (0.33): app.py no longer contains the broken variable/route name
    # Based on task factory, possible broken routes are ["/users", "/orders", "/products"]
    app_content = state.filesystem.get("app.py", "")
    broken_targets = ["/users", "/orders", "/products"]
    if all(target not in app_content for target in broken_targets):
        score += 0.33
        
    # Check 3 (0.34): app.py is valid Python (use ast.parse — catch SyntaxError)
    try:
        if app_content:
            ast.parse(app_content)
            score += 0.34
    except SyntaxError:
        pass
        
    return round(score, 2)

def grade_hard(state: StateModel) -> float:
    """
    Grades the hard task: Multiple fixes (packages, env vars, syntax, reads).
    """
    score = 0.0
    
    # Check 1 (0.2): all required packages in state.installed_packages
    if all(pkg in state.installed_packages for pkg in state.required_packages):
        score += 0.2
        
    # Check 2 (0.2): .env values are both corrected
    if all(state.env_vars.get(k) == v for k, v in state.required_env_vars.items()):
        score += 0.2
        
    # Check 3 (0.2): app.py has no syntax error (ast.parse)
    app_content = state.filesystem.get("app.py", "")
    try:
        if app_content:
            ast.parse(app_content)
            score += 0.2
    except SyntaxError:
        pass
        
    # Check 4 (0.2): app.py contains correct imports
    if all(f"import {pkg}" in app_content for pkg in state.required_packages):
        score += 0.2
        
    # Check 5 (0.2): logs.txt has been read (in state.files_read)
    if "logs.txt" in state.files_read:
        score += 0.2
        
    return round(score, 2)

def grade(task_id: str, state: StateModel) -> float:
    """
    Routes to the correct grader by task_id.
    """
    if task_id == "easy_missing_dep":
        return grade_easy(state)
    elif task_id == "medium_config_route":
        return grade_medium(state)
    elif task_id == "hard_multi_failure":
        return grade_hard(state)
    return 0.0
