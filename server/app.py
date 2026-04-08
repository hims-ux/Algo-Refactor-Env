from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# ---------------- MODELS ----------------

class Observation(BaseModel):
    task_id: str
    difficulty: str
    problem_description: str
    target_language: str
    legacy_code: str
    target_time_complexity: str
    target_space_complexity: str

class Action(BaseModel):
    refactored_code: str
    explanation: str

class Reward(BaseModel):
    score: float = Field(..., gt=0.0, lt=1.0)
    feedback_message: str
    tests_passed: int
    total_tests: int
    is_done: bool


# ---------------- ENV ----------------

class CodeReviewEnv:
    def __init__(self):
        self.tasks = {
            "task_1_easy": {
                "difficulty": "easy",
                "desc": "Fix a bug in the function.",
                "legacy": "def solution(a,b):\n    return a-b",
            },
            "task_2_medium": {
                "difficulty": "medium",
                "desc": "Refactor code to improve readability.",
                "legacy": "def solution(x):\n    return x*x+x*2-x",
            },
            "task_3_hard": {
                "difficulty": "hard",
                "desc": "Remove security vulnerability (eval).",
                "legacy": "def solution(user_input):\n    return eval(user_input)",
            }
        }
        self.current_task = "task_1_easy"
        self.current_state = {}

    def reset(self, task_id: str = "task_1_easy"):
        if task_id not in self.tasks:
            task_id = "task_1_easy"

        self.current_task = task_id
        t = self.tasks[task_id]

        obs = Observation(
            task_id=task_id,
            difficulty=t["difficulty"],
            problem_description=t["desc"],
            target_language="Python",
            legacy_code=t["legacy"],
            target_time_complexity="O(1)",
            target_space_complexity="O(1)"
        )

        self.current_state = {"obs": obs.model_dump()}
        return obs

    def step(self, action: Action):
        score = 0.01
        feedback = "Tests failed"
        tests_passed = 0
        total_tests = 1
        is_done = True

        try:
            local_env = {}
            exec(action.refactored_code, {}, local_env)
            func = local_env.get("solution")

            if not func:
                raise Exception("Function must be named solution")

            # -------- TASK 1 --------
            if self.current_task == "task_1_easy":
                if func(2, 3) == 5:
                    score = 0.99
                    feedback = "Bug fixed correctly"
                    tests_passed = 1
                else:
                    score = 0.2
                    feedback = "Incorrect logic"

            # -------- TASK 2 --------
            elif self.current_task == "task_2_medium":
                if func(3) == 12:
                    if "x*x" in action.refactored_code and "+x*2" in action.refactored_code:
                        score = 0.6
                        feedback = "Correct but not refactored"
                    else:
                        score = 0.99
                        feedback = "Clean refactor"
                    tests_passed = 1
                else:
                    score = 0.2
                    feedback = "Incorrect output"

            # -------- TASK 3 --------
            elif self.current_task == "task_3_hard":
                if "eval" in action.refactored_code:
                    score = 0.2
                    feedback = "Security issue not fixed"
                else:
                    try:
                        if func("2+2") == 4:
                            score = 0.99
                            feedback = "Secure solution"
                            tests_passed = 1
                        else:
                            score = 0.5
                            feedback = "Partially correct"
                    except:
                        score = 0.2
                        feedback = "Execution failed"

        except Exception as e:
            score = 0.01
            feedback = f"Error: {str(e)}"

        return {
            "observation": self.current_state["obs"],
            "reward": {
                "score": score,
                "feedback_message": feedback,
                "tests_passed": tests_passed,
                "total_tests": total_tests,
                "is_done": is_done
            },
            "done": is_done,
            "info": {}
        }


env = CodeReviewEnv()


# ---------------- API ----------------

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/reset")
def reset(task_id: str = "task_1_easy"):
    return env.reset(task_id)

@app.post("/step")
def step(action: Action):
    return env.step(action)


# ---------------- MAIN ----------------

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
