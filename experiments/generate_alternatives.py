import ast
import json
import re
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INPUT = ROOT / "data/code_submissions.json"
OUTPUT = ROOT / "data/alternative_submissions.json"

MODEL = "qwen2.5-coder:3b"


def generate(question):
    prompt = f"""
You are an expert Python programmer.

Solve this programming problem:

{question}

Requirements:
- Write a complete Python function.
- Use a reasonable implementation approach.
- Handle edge cases.
- Include a docstring.
- Return only Python code inside a Python code block.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7}
        },
        timeout=300
    )

    response.raise_for_status()
    raw = response.json()["response"]

    match = re.search(
        r"```(?:python)?\s*(.*?)```",
        raw,
        re.DOTALL | re.IGNORECASE
    )

    if not match:
        raise ValueError("No Python code block returned")

    code = match.group(1).strip()
    ast.parse(code)

    return code


def main():
    with open(INPUT, encoding="utf-8") as file:
        submissions = json.load(file)

    alternatives = []

    for item in submissions:
        print("Generating:", item["question_id"])

        try:
            code = generate(item["question"])

            alternatives.append({
                "submission_id": item["question_id"] + "_S02",
                "question_id": item["question_id"],
                "question": item["question"],
                "generator_model": MODEL,
                "prompt_version": "alternative_v1",
                "code": code
            })

            print("SUCCESS")

        except Exception as error:
            print("FAILED:", error)

    with open(OUTPUT, "w", encoding="utf-8") as file:
        json.dump(alternatives, file, indent=4)

    print("\nGenerated alternatives:", len(alternatives))
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()
