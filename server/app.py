from fastapi import FastAPI
from pydantic import BaseModel
import random

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


# ---------------- ENV ----------------

class CodeReviewEnv:
    def __init__(self):
        self.tasks = {
            "task_1_easy": {
                "difficulty": "easy",
                "desc": "Fix subtraction bug",
                "legacy": "def solution(a,b):\n    return a-b",
                "expected": "return a+b"
            },
            "task_2_easy": {
                "difficulty": "easy",
                "desc": "Fix multiplication bug",
                "legacy": "def solution(a,b):\n    return a+b",
                "expected": "return a*b"
            },
            "task_3_easy": {
                "difficulty": "easy",
                "desc": "Fix division bug",
                "legacy": "def solution(a,b):\n    return a*b",
                "expected": "return a/b"
            }
        }

        self.current_state = {}

    # ---------------- RESET ----------------
    def reset(self, task_id: str = None):
        if task_id is None or task_id not in self.tasks:
            task_id = random.choice(list(self.tasks.keys()))

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

        # store state safely
        self.current_state = {"obs": obs.model_dump()}

        return obs

    # ---------------- STEP ----------------
    def step(self, action: Action):
        # ensure state exists
        if "obs" not in self.current_state:
            obs = self.reset()
        else:
            obs = self.current_state["obs"]

        # handle dict safely
        task_id = obs["task_id"]
        expected = self.tasks[task_id]["expected"]

        code = action.refactored_code.lower()

        # grading
        if expected in code:
            score = random.uniform(0.7, 0.95)
            feedback = "Correct fix"
            passed = 1
        else:
            score = random.uniform(0.1, 0.4)
            feedback = "Incorrect fix"
            passed = 0

        return {
            "observation": obs,
            "reward": {
                "score": score,
                "feedback_message": feedback,
                "tests_passed": passed,
                "total_tests": 1,
                "is_done": True
            },
            "done": True,
            "info": {}
        }


# global env
env = CodeReviewEnv()

# ---------------- API ----------------

@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/reset")
def reset(task_id: str = None):
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
