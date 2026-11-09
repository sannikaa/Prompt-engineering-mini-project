import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


# Project paths
ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_FILE = ROOT / "data" / "coding_questions.csv"
OUTPUT_FILE = ROOT / "data" / "code_submissions.json"

# Generator model
MODEL = "qwen2.5-coder:3b"

# Ollama local API
OLLAMA_URL = "http://localhost:11434/api/generate"


def extract_code(response):
    """Extract Python code from an LLM response."""

    # Find code inside Markdown code blocks
    match = re.search(
        r"```(?:python)?\s*(.*?)```",
        response,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    # If no code block exists, use the complete response
    return response.strip()


def generate_code(question):
    """Generate a Python solution using Ollama."""

    prompt = f"""
You are an expert Python programmer.

Solve the following programming problem.

Problem:
{question}

Requirements:
1. Write a complete Python function.
2. Use clear variable and function names.
3. Handle important edge cases.
4. Avoid unnecessary complexity.
5. Include a short docstring.
6. Do not include example usage or explanations.
7. Return only the Python code inside a Python code block.

Generate the solution now.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2
                }
            },
            timeout=300
        )

        response.raise_for_status()

        result = response.json()
        raw_response = result.get("response", "")

        if not raw_response.strip():
            raise ValueError("The model returned an empty response.")

        code = extract_code(raw_response)

        return code, raw_response

    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not connect to Ollama: {error}"
        ) from error


def main():
    """Generate solutions for all questions and save them."""

    if not QUESTIONS_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {QUESTIONS_FILE}"
        )

    questions = pd.read_csv(QUESTIONS_FILE)

    submissions = []

    print("\nAI CODE GENERATION STARTED")
    print("=" * 50)

    for _, row in questions.iterrows():

        question_id = row["question_id"]
        question = row["question"]

        print(f"\nGenerating solution for {question_id}...")

        try:
            code, raw_response = generate_code(question)

            submission = {
                "submission_id": f"{question_id}_S01",
                "question_id": question_id,
                "question": question,
                "topic": row["topic"],
                "difficulty": row["difficulty"],
                "generator_model": MODEL,
                "prompt_version": "generator_v1",
                "code": code,
                "raw_response": raw_response,
                "generated_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }

            submissions.append(submission)

            print(f"SUCCESS: {question_id}")

        except Exception as error:
            print(f"FAILED: {question_id}")
            print(f"Reason: {error}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(submissions, file, indent=4, ensure_ascii=False)

    print("\n" + "=" * 50)
    print("GENERATION COMPLETED")
    print(f"Total questions: {len(questions)}")
    print(f"Successful submissions: {len(submissions)}")
    print(f"Failed submissions: {len(questions) - len(submissions)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
