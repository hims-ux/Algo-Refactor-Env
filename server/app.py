from fastapi import FastAPI
from pydantic import BaseModel

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
        import random
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

        self.current_state = {"obs": obs.model_dump()}

        return obs

    # ---------------- STEP ----------------
    def step(self, action: Action):
    # Always safe score regardless of state
    code = action.refactored_code.lower()
    
    correct_answers = ["return a+b", "return a*b", "return a/b"]
    is_correct = any(ans in code for ans in correct_answers)

    score = 0.85 if is_correct else 0.35

    return {
        "observation": self.current_state.get("obs", {}),
        "reward": {
            "score": score,
            "feedback_message": "Correct fix" if is_correct else "Incorrect fix",
            "tests_passed": 1 if is_correct else 0,
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
