from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import time
import ast

app = FastAPI()

# --- 1. OPENENV PYDANTIC MODELS ---
class Observation(BaseModel):
    task_id: str
    difficulty: str
    problem_description: str
    target_language: str
    legacy_code: str
    last_error_log: Optional[str] = None
    target_time_complexity: str
    target_space_complexity: str

class Action(BaseModel):
    refactored_code: str
    explanation: str = Field(..., description="Explanation of optimizations.")

class Reward(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    feedback_message: str
    tests_passed: int
    total_tests: int
    is_done: bool

# --- 2. ENVIRONMENT LOGIC & GRADERS ---
class AlgoRefactorEnv:
    def __init__(self):
        self.tasks = {
            "task_1_easy": {
                "difficulty": "easy",
                "desc": "Optimize the Two-Sum algorithm. Find two numbers that add up to the target.",
                "language": "Python",
                "legacy": "def solution(arr, target):\n    for i in range(len(arr)):\n        for j in range(i+1, len(arr)):\n            if arr[i] + arr[j] == target:\n                return [i, j]\n    return []",
                "target_tc": "O(N)",
                "target_sc": "O(N)"
            },
            "task_2_medium": {
                "difficulty": "medium", 
                "desc": "Refactor the Nth Fibonacci number function. The legacy code uses slow O(2^N) recursion.", 
                "language": "Python", 
                "legacy": "def solution(n):\n    if n <= 1: return n\n    return solution(n-1) + solution(n-2)", 
                "target_tc": "O(N)", 
                "target_sc": "O(1)"
            },
            "task_3_hard": {
                "difficulty": "hard", 
                "desc": "Find the duplicate number in an array of size n+1 containing integers 1 to n. You must not modify the array or use extra space.", 
                "language": "Python", 
                "legacy": "def solution(arr):\n    seen = set()\n    for num in arr:\n        if num in seen: return num\n        seen.add(num)\n    return -1", 
                "target_tc": "O(N)", 
                "target_sc": "O(1)"
            }
        }
        self.current_state = {}
        self.current_task = "task_1_easy"

    def reset(self, task_id: str = "task_1_easy") -> Observation:
        if task_id not in self.tasks: task_id = "task_1_easy"
        self.current_task = task_id
        t = self.tasks[task_id]
        obs = Observation(
            task_id=task_id, difficulty=t["difficulty"], problem_description=t["desc"],
            target_language=t["language"], legacy_code=t["legacy"],
            target_time_complexity=t["target_tc"], target_space_complexity=t["target_sc"]
        )
        self.current_state = {"obs": obs.model_dump()}
        return obs

    def step(self, action: Action) -> dict:
        score = 0.0
        feedback = "Tests failed."
        is_done = True
        tests_passed = 0
        total_tests = 3
        
        try:
            local_env = {}
            exec(action.refactored_code, {}, local_env)
            func = local_env.get('solution')
            if not func: raise ValueError("Function must be named 'solution'")

            # GRADER FOR TASK 1 (Two Sum -> O(N) time)
            if self.current_task == "task_1_easy":
                if func([2, 7, 11, 15], 9) == [0, 1] or func([2, 7, 11, 15], 9) == [1, 0]: tests_passed += 1
                if func([3, 2, 4], 6) == [1, 2] or func([3, 2, 4], 6) == [2, 1]: tests_passed += 1
                
                start_time = time.time()
                func(list(range(5000)), -1) # Stress test
                exec_time = time.time() - start_time
                
                if tests_passed == 2:
                    if exec_time < 0.05:
                        tests_passed += 1; score = 1.0; feedback = "O(N) time complexity achieved using Hash Map."
                    else:
                        score = 0.6; feedback = "Correct, but too slow (O(N^2))."

            # GRADER FOR TASK 2 (Fibonacci -> O(N) time, O(1) space)
            elif self.current_task == "task_2_medium":
                if func(2) == 1: tests_passed += 1
                if func(10) == 55: tests_passed += 1
                
                start_time = time.time()
                ans = func(1000) # Recursion would crash/hang here
                exec_time = time.time() - start_time
                
                if tests_passed == 2:
                    if exec_time < 0.01:
                        tests_passed += 1; score = 1.0; feedback = "O(N) iterative solution achieved."
                    else:
                        score = 0.5; feedback = "Correct logic, but recursion limit or time limit exceeded."

            # GRADER FOR TASK 3 (Duplicate Number -> O(N) time, O(1) space)
            elif self.current_task == "task_3_hard":
                if func([1, 3, 4, 2, 2]) == 2: tests_passed += 1
                if func([3, 1, 3, 4, 2]) == 3: tests_passed += 1
                
                # Check for illegal O(N) space usage by parsing the code
                illegal_space = any(word in action.refactored_code for word in ["set(", "dict(", "[]", "{}"])
                
                if tests_passed == 2:
                    if not illegal_space:
                        tests_passed += 1; score = 1.0; feedback = "Perfect! O(1) space achieved (e.g., using Floyd's Tortoise and Hare)."
                    else:
                        score = 0.7; feedback = "Correct, but you used extra memory. Target is O(1) space."

        except Exception as e:
            score = 0.0
            feedback = f"Execution Error: {str(e)}"

        rew = Reward(score=score, feedback_message=feedback, tests_passed=tests_passed, total_tests=total_tests, is_done=is_done)
        return {"observation": self.current_state["obs"], "reward": rew.model_dump(), "done": is_done, "info": {}}

env = AlgoRefactorEnv()

# --- 3. API ENDPOINTS ---
@app.get("/")
def health_check(): return {"status": "ok"}

@app.post("/reset")
def reset(task_id: str = "task_1_easy"): return env.reset(task_id)

@app.get("/state")
def state(): return env.current_state

@app.post("/step")
def step(action: Action): return env.step(action)

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == '__main__':
    main()
