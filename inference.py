import os
import requests
from openai import OpenAI

# --- CORRECTED ENVIRONMENT VARIABLES ---
API_BASE_URL = os.environ.get("API_BASE_URL")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
API_KEY = os.environ.get("API_KEY")

ENV_URL = "https://himanshu2100-algo-refactor-env.hf.space"
TASK_NAME = "task_1_easy"
BENCHMARK = "algo-refactor-env"
# Initialize the client using the injected variables
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

def run_baseline():
    # --- 1. MANDATORY [START] FORMAT ---
    print(f"[START] task={TASK_NAME} env={BENCHMARK} model={MODEL_NAME}", flush=True)

    # Setup Environment
    res = requests.post(f"{ENV_URL}/reset?task_id={TASK_NAME}").json()
    legacy_code = res.get('legacy_code', '')
    
    prompt = f"Fix this Python code to be O(N) time and O(N) space. Only return the python function named 'solution'.\n{legacy_code}"
    
    # Run LLM
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        code = completion.choices[0].message.content.replace('```python', '').replace('```', '').strip()
    except Exception:
        code = "def solution(arr, target):\n    return []" # Fallback if API fails
        
    # Send Action to Environment
    action_payload = {"refactored_code": code, "explanation": "Refactored algorithm."}
    step_res = requests.post(f"{ENV_URL}/step", json=action_payload).json()
    
    reward = float(step_res.get('reward', {}).get('score', 0.0))
    done = step_res.get('done', True)
    error = step_res.get('reward', {}).get('feedback_message', "null")
    
    # --- 2. MANDATORY [STEP] FORMAT ---
    done_val = str(done).lower()
    error_val = f"'{error}'" if error else "null"
    print(f"[STEP] step=1 action='submit_refactor' reward={reward:.2f} done={done_val} error={error_val}", flush=True)
    
    # --- 3. MANDATORY [END] FORMAT ---
    success = str(reward >= 1.0).lower()
    print(f"[END] success={success} steps=1 rewards={reward:.2f}", flush=True)

if __name__ == "__main__":
    run_baseline()
