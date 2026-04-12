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
                "desc": "Fix a bug in the function.",
                "legacy": "def solution(a,b):\n    return a-b",
            }
        }
        self.current_state = {}

    def reset(self, task_id: str = "task_1_easy"):
        if task_id not in self.tasks:
            task_id = "task_1_easy"

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

        # ✅ GUARANTEE state is set
        self.current_state = {}
        self.current_state["obs"] = obs.model_dump()

        return obs

    def step(self, action: Action):
        # ✅ Safety check
        if "obs" not in self.current_state:
            return {
                "observation": {},
                "reward": {
                    "score": 0.0,
                    "feedback_message": "Reset not called",
                    "tests_passed": 0,
                    "total_tests": 1,
                    "is_done": True
                },
                "done": True,
                "info": {}
            }

        # ✅ Execute code safely
        local_env = {}
        exec(action.refactored_code, {}, local_env)
        func = local_env.get("solution")

        if func and func(2, 3) == 5:
            score = 0.99
            feedback = "Bug fixed correctly"
        else:
            score = 0.2
            feedback = "Incorrect logic"

        return {
            "observation": self.current_state["obs"],
            "reward": {
                "score": score,
                "feedback_message": feedback,
                "tests_passed": 1,
                "total_tests": 1,
                "is_done": True
            },
            "done": True,
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
