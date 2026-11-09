import ast
import json
import re
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INPUT = ROOT / "data/coding_questions.csv"
OUTPUT = ROOT / "data/judge_model_submissions.json"

import pandas as pd

MODEL = "qwen2.5:7b"


def generate(question):
    prompt = f"""
You are an expert Python programmer.

Solve this problem:

{question}

Write a complete Python function.
Handle edge cases.
Include a docstring.
Return only Python code inside a Python code block.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2}
        },
        timeout=600
    )

    response.raise_for_status()
    raw = response.json()["response"]

    match = re.search(
        r"```(?:python)?\s*(.*?)```",
        raw,
        re.DOTALL | re.IGNORECASE
    )

    if not match:
        raise ValueError("No code block returned")

    code = match.group(1).strip()
    ast.parse(code)

    return code


def main():
    questions = pd.read_csv(INPUT)
    results = []

    for _, row in questions.iterrows():
        print("Generating:", row["question_id"])

        try:
            code = generate(row["question"])

            results.append({
                "submission_id": row["question_id"] + "_S03",
                "question_id": row["question_id"],
                "question": row["question"],
                "generator_model": MODEL,
                "code": code
            })

            print("SUCCESS")

        except Exception as error:
            print("FAILED:", error)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print("\nJudge-model submissions:", len(results))


if __name__ == "__main__":
    main()
