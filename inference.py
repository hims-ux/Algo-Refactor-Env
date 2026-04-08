import os
import requests
from openai import OpenAI

# --- ENVIRONMENT VARIABLES ---
API_BASE_URL = os.environ.get("API_BASE_URL")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
API_KEY = os.environ.get("API_KEY")

# Make sure this matches your hugging face space URL exactly
ENV_URL = "https://himanshu2100-algo-refactor-env.hf.space"
BENCHMARK = "algo-refactor-env"

# All three tasks required by the grader
TASKS = ["task_1_easy", "task_2_medium", "task_3_hard"]

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

def run_baseline():
    # Loop through all 3 tasks to satisfy the grader requirement
    for task_name in TASKS:
        # --- 1. MANDATORY [START] FORMAT ---
        print(f"[START] task={task_name} env={BENCHMARK} model={MODEL_NAME}", flush=True)

        # Setup Environment for the specific task
        try:
            res = requests.post(f"{ENV_URL}/reset?task_id={task_name}").json()
            legacy_code = res.get('legacy_code', '')
        except Exception as e:
            legacy_code = ""

        prompt = f"Fix this Python code to be optimized. Only return the python function named 'solution'.\n{legacy_code}"

        # Run LLM
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}]
            )
            code = completion.choices[0].message.content.replace('```python', '').replace('```', '').strip()
        except Exception:
            # Fallback code if LLM fails
            code = "def solution(*args, **kwargs):\n    pass"

        # Send Action to Environment
        action_payload = {"refactored_code": code, "explanation": "Refactored algorithm."}
        
        try:
            step_res = requests.post(f"{ENV_URL}/step", json=action_payload).json()
            
            # CRITICAL FIX: Default to 0.01 instead of 0.0 if something goes wrong
            reward = float(step_res.get('reward', {}).get('score', 0.01))
            done = step_res.get('done', True)
            error = step_res.get('reward', {}).get('feedback_message', "null")
        except Exception as e:
            reward = 0.01
            done = True
            error = str(e)

        # CRITICAL FIX: Enforce strict bounds (cannot be exactly 0.0 or 1.0)
        if reward <= 0.0: reward = 0.01
        if reward >= 1.0: reward = 0.99

        # --- 2. MANDATORY [STEP] FORMAT ---
        done_val = str(done).lower()
        error_val = f"'{error}'" if error and error != "null" else "null"
        print(f"[STEP] step=1 action='submit_refactor' reward={reward:.2f} done={done_val} error={error_val}", flush=True)

        # --- 3. MANDATORY [END] FORMAT ---
        # Success is determined if reward is high (e.g., >= 0.90), not just exactly 1.0
        success = str(reward >= 0.90).lower()
        print(f"[END] success={success} steps=1 rewards={reward:.2f}", flush=True)

if __name__ == "__main__":
    run_baseline()
