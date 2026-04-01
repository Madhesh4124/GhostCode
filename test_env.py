# Test suite for the GhostCode environment
import sys
import os

# Add the current directory to sys.path to ensure local modules are found
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from env.environment import GhostCodeEnv
from models.models import ActionModel

def test_easy():
    print("\n--- Testing Easy Task: easy_missing_dep ---")
    env = GhostCodeEnv(verbose=True)
    obs = env.reset("easy_missing_dep", seed=42)
    
    # 1. Read logs (Investigate)
    action = ActionModel(action_type="read_file", path="logs.txt")
    env.step(action)
    
    # 2. Install pandas (Dependency fix)
    action = ActionModel(action_type="install_package", package="pandas")
    env.step(action)
    
    # 3. Write fixed app.py (Code fix: Add import and valid code)
    content = "import pandas\ndef process_data():\n    return pandas.head()\n"
    action = ActionModel(action_type="write_file", path="app.py", content=content)
    obs, reward, done, info = env.step(action)
    
    score = info.get("grade", 0.0)
    print(f"Final Score: {score}")
    assert score == 1.0, f"Expected score 1.0, got {score}"
    print("PASS: Easy task solved successfully.")

def test_medium():
    print("\n--- Testing Medium Task: medium_config_route ---")
    env = GhostCodeEnv(verbose=True)
    obs = env.reset("medium_config_route", seed=42)
    
    # 1. Read logs (Investigate)
    action = ActionModel(action_type="read_file", path="logs.txt")
    env.step(action)
    
    # 2. Fix .env (Configuration fix)
    action = ActionModel(action_type="write_file", path=".env", content="DB_PATH=/app/db.sqlite\n")
    env.step(action)
    
    # 3. Fix app.py (Route/Variable fix: Remove randomized broken strings)
    # Replacing with a clean app that doesn't contain any of the broken route names
    content = "import os\nfrom flask import Flask\n\napp = Flask(__name__)\n\n@app.route('/')\ndef route():\n    return 'Hello World'\n"
    action = ActionModel(action_type="write_file", path="app.py", content=content)
    obs, reward, done, info = env.step(action)
    
    score = info.get("grade", 0.0)
    print(f"Final Score: {score}")
    assert score == 1.0, f"Expected score 1.0, got {score}"
    print("PASS: Medium task solved successfully.")

def test_hard():
    print("\n--- Testing Hard Task: hard_multi_failure ---")
    env = GhostCodeEnv(verbose=True)
    obs = env.reset("hard_multi_failure", seed=42)
    state = env.state()
    
    # 1. Read logs (Required exploration for score)
    action = ActionModel(action_type="read_file", path="logs.txt")
    env.step(action)
    
    # 2. Install each required package dynamically from state
    for pkg in state.required_packages:
        action = ActionModel(action_type="install_package", package=pkg)
        env.step(action)
        
    # 3. Fix .env with all correct values dynamically from state
    env_content = ""
    for k, v in state.required_env_vars.items():
        env_content += f"{k}={v}\n"
    action = ActionModel(action_type="write_file", path=".env", content=env_content)
    env.step(action)
    
    # 4. Fix app.py (Syntax + correct Imports)
    app_content = "import os\n"
    for pkg in state.required_packages:
        app_content += f"import {pkg}\n"
    app_content += "def main():\n    pass\n"
    action = ActionModel(action_type="write_file", path="app.py", content=app_content)
    obs, reward, done, info = env.step(action)
    
    score = info.get("grade", 0.0)
    print(f"Final Score: {score}")
    assert score == 1.0, f"Expected score 1.0, got {score}"
    print("PASS: Hard task solved successfully.")

if __name__ == "__main__":
    print("Starting GhostCode Environment Validation...")
    try:
        test_easy()
        test_medium()
        test_hard()
        print("\n" + "="*40)
        print("ALL SYSTEM VALIDATION TESTS: PASSED")
        print("="*40)
    except AssertionError as e:
        print(f"\nFAIL: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\nCRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
