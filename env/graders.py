# Task grading and evaluation logic
import ast
from models.models import StateModel

def grade_easy(state: StateModel) -> float:
    """
    Grades the easy task: pandas installation and import.
    """
    score = 0.0
    # Check 1 (0.49): "pandas" is in state.installed_packages
    if "pandas" in state.installed_packages:
        score += 0.49
    
    # Check 2 (0.49): state.filesystem["app.py"] contains "import pandas"
    app_content = state.filesystem.get("app.py", "")
    if "import pandas" in app_content:
        score += 0.49
        
    score = round(score, 4)

    if score <= 0.0:
        return 0.01

    score = round(score, 2)

    if score >= 1.0:
        return 0.99

    return score

def grade_medium(state: StateModel) -> float:
    """
    Grades the medium task: DB_PATH config and route fix.
    """
    score = 0.0
    # Check 1 (0.32): state.env_vars["DB_PATH"] == "/app/db.sqlite"
    if state.env_vars.get("DB_PATH") == "/app/db.sqlite":
        score += 0.32
        
    # Check 2 (0.32): app.py no longer contains the broken variable/route name
    # Based on task factory, possible broken routes are ["/users", "/orders", "/products"]
    app_content = state.filesystem.get("app.py", "")
    broken_targets = ["/users", "/orders", "/products"]
    if all(target not in app_content for target in broken_targets):
        score += 0.32
        
    # Check 3 (0.34): app.py is valid Python (use ast.parse — catch SyntaxError)
    try:
        if app_content:
            ast.parse(app_content)
            score += 0.34
    except SyntaxError:
        pass
        
    score = round(score, 4)

    if score <= 0.0:
        return 0.01

    score = round(score, 2)

    if score >= 1.0:
        return 0.99

    return score

def grade_hard(state: StateModel) -> float:
    """
    Grades the hard task: Multiple fixes (packages, env vars, syntax, reads).
    """
    score = 0.0
    
    # Check 1 (0.19): all required packages in state.installed_packages
    if all(pkg in state.installed_packages for pkg in state.required_packages):
        score += 0.19
        
    # Check 2 (0.19): .env values are both corrected
    if all(state.env_vars.get(k) == v for k, v in state.required_env_vars.items()):
        score += 0.19
        
    # Check 3 (0.19): app.py has no syntax error (ast.parse)
    app_content = state.filesystem.get("app.py", "")
    try:
        if app_content:
            ast.parse(app_content)
            score += 0.19
    except SyntaxError:
        pass
        
    # Check 4 (0.19): app.py contains correct imports
    if all(f"import {pkg}" in app_content for pkg in state.required_packages):
        score += 0.19
        
    # Check 5 (0.19): logs.txt has been read (in state.files_read)
    if "logs.txt" in state.files_read:
        score += 0.19
        
    score = round(score, 4)

    if score <= 0.0:
        return 0.01

    score = round(score, 2)

    if score >= 1.0:
        return 0.99

    return score

def grade(task_id: str, state: StateModel) -> float:
    """
    Routes to the correct grader by task_id.
    """
    score = 0.0
    if task_id == "easy_missing_dep":
        score = grade_easy(state)
    elif task_id == "medium_config_route":
        score = grade_medium(state)
    elif task_id == "hard_multi_failure":
        score = grade_hard(state)
    
    # Ensure score is strictly between 0 and 1
    return max(0.01, min(0.99, score))
