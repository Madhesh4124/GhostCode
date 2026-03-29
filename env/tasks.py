# Task management and definition logic
import random

def make_easy_task(seed: int) -> dict:
    """
    Creates an easy task with a missing pandas import.
    """
    rng = random.Random(seed)
    var_name = rng.choice(["df", "data", "frame"])
    pkg_alias = rng.choice(["pd", "pandas"])
    line_num = rng.randint(5, 50)
    
    app_content = f"# Sample app using {pkg_alias}\n\ndef process_data():\n    # Bug: using {var_name} without import\n    return {var_name}.head()\n"
    logs_content = f"ERROR at line {line_num}: NameError: name '{var_name}' is not defined. Tried to use {pkg_alias} via {var_name}."
    
    return {
        "task_id": "easy_missing_dep",
        "difficulty": "easy",
        "description": f"The application is trying to use pandas via '{var_name}', but the import is missing.",
        "initial_files": {
            "app.py": app_content,
            "logs.txt": logs_content,
            "requirements.txt": "pandas\n"
        },
        "required_reads": ["app.py", "logs.txt"],
        "required_packages": ["pandas"],
        "required_env_vars": {},
        "solution": {"type": "fix_import", "at": "app.py"},
        "max_steps": 10
    }

def make_medium_task(seed: int) -> dict:
    """
    Creates a medium task with a wrong DB path and a broken route name.
    """
    rng = random.Random(seed)
    wrong_db_path = rng.choice(["/tmp/db.sqlite", "/var/db.sqlite", "/old/db.sqlite"])
    broken_route = rng.choice(["/users", "/orders", "/products"])
    
    app_content = (
        f"import os\nfrom flask import Flask\n\napp = Flask(__name__)\n\n"
        f"@app.route('{broken_route}')\ndef route():\n    # Broken route needs fix\n    return 'Hello World'\n\n"
        f"if __name__ == '__main__':\n    db = os.getenv('DB_PATH')\n    print(f'Connecting to {{db}}')\n"
    )
    env_content = f"DB_PATH={wrong_db_path}\n"
    logs_content = f"ERROR: Failed to connect to database at {wrong_db_path}. No such path. Broken endpoint hit: {broken_route}."
    
    return {
        "task_id": "medium_config_route",
        "difficulty": "medium",
        "description": "The database path in .env is incorrect and a critical route is misconfigured.",
        "initial_files": {
            "app.py": app_content,
            ".env": env_content,
            "logs.txt": logs_content
        },
        "required_reads": [".env", "app.py", "logs.txt"],
        "required_packages": [],
        "required_env_vars": {"DB_PATH": "/app/db.sqlite"},
        "solution": {"type": "fix_config_and_route"},
        "max_steps": 20
    }

def make_hard_task(seed: int) -> dict:
    """
    Creates a hard task with a syntax error, missing packages, and multiple wrong env vars.
    """
    rng = random.Random(seed)
    all_packages = ["pandas", "requests", "sqlalchemy", "pydantic"]
    chosen_pkgs = rng.sample(all_packages, 2)
    
    env_vars_config = {
        "DB_PATH": "/app/db.sqlite", 
        "API_KEY": "ghost_secret", 
        "PORT": "8080"
    }
    chosen_env_keys = rng.sample(list(env_vars_config.keys()), 2)
    
    wrong_env_vars = {}
    correct_env_vars = {}
    for key in chosen_env_keys:
        correct_env_vars[key] = env_vars_config[key]
        if key == "DB_PATH":
            wrong_env_vars[key] = "/wrong/path"
        elif key == "API_KEY":
            wrong_env_vars[key] = "wrong_key_123"
        else: # PORT
            wrong_env_vars[key] = "9999"

    app_content = "def broken_function()\n    # Missing colon above\n    import non_existent_pkg\n"
    for pkg in chosen_pkgs:
        app_content += f"# Missing import for {pkg}\n"
        
    env_content = "\n".join([f"{k}={v}" for k, v in wrong_env_vars.items()])
    
    line_syntax = rng.randint(1, 5)
    line_import = rng.randint(10, 20)
    logs_content = (
        f"CRITICAL SyntaxError at line {line_syntax}: expected ':'\n"
        f"ModuleNotFoundError: No module named '{chosen_pkgs[0]}' at line {line_import}\n"
    )
    
    return {
        "task_id": "hard_multi_failure",
        "difficulty": "hard",
        "description": "A catastrophic failure: syntax errors in app.py, missing packages in requirements, and incorrect environment variables.",
        "initial_files": {
            "app.py": app_content,
            ".env": env_content,
            "requirements.txt": "Flask\n",
            "logs.txt": logs_content
        },
        "required_reads": ["app.py", ".env", "requirements.txt", "logs.txt"],
        "required_packages": chosen_pkgs,
        "required_env_vars": correct_env_vars,
        "solution": {"type": "complex_fix"},
        "max_steps": 35
    }

def get_task(task_id: str, seed: int = 42) -> dict:
    """
    Retrieves a task by its ID and seed.
    """
    if task_id == "easy_missing_dep":
        return make_easy_task(seed)
    elif task_id == "medium_config_route":
        return make_medium_task(seed)
    elif task_id == "hard_multi_failure":
        return make_hard_task(seed)
    else:
        raise ValueError(f"Unknown task_id: {task_id}")
