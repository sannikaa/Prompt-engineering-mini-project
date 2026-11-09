import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT / "data" / "code_submissions.json"
PROMPT_FILE = ROOT / "prompts" / "structured_rubric.txt"
OUTPUT_FILE = ROOT / "data" / "judge_evaluations.json"

MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/generate"

DIMENSIONS = [
    "correctness",
    "security",
    "readability",
    "efficiency"
]


def load_prompt():
    """Load the structured evaluation prompt."""

    with open(PROMPT_FILE, "r", encoding="utf-8") as file:
        return file.read()


def extract_json(response):
    """Extract JSON from the model response."""

    # Remove Markdown code fences if present
    cleaned = re.sub(
        r"```(?:json)?",
        "",
        response,
        flags=re.IGNORECASE
    ).replace("```", "").strip()

    # Locate the JSON object
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model response.")

    return json.loads(cleaned[start:end + 1])


def validate_evaluation(result):
    """Check that all evaluation scores are valid."""

    for dimension in DIMENSIONS:
        if dimension not in result:
            raise ValueError(
                f"Missing evaluation dimension: {dimension}"
            )

        score = result[dimension]

        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError(
                f"Invalid score for {dimension}: {score}"
            )

        if not 0 <= score <= 10:
            raise ValueError(
                f"Score out of range for {dimension}: {score}"
            )

    return result


def evaluate_code(question, code, prompt_template):
    """Ask the judge model to evaluate one code submission."""

    prompt = (
        prompt_template
        .replace("{question}", question)
        .replace("{code}", code)
    )

    prompt += """

IMPORTANT OUTPUT REQUIREMENTS:
- Return only one valid JSON object.
- All four scores must be numbers between 0 and 10.
- Do not use a score out of 5.
- Include explanations for all four dimensions.
- Do not include Markdown outside the JSON.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0
            }
        },
        timeout=600
    )

    response.raise_for_status()

    raw_response = response.json().get("response", "")

    result = extract_json(raw_response)
    result = validate_evaluation(result)

    # Calculate overall score ourselves
    scores = [result[dimension] for dimension in DIMENSIONS]

    result["overall_score"] = round(sum(scores) / 4, 2)

    return result, raw_response


def main():
    """Evaluate all generated code submissions."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError("Code submissions dataset not found.")

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        submissions = json.load(file)

    prompt_template = load_prompt()

    evaluations = []

    print("\nAI CODE JUDGING STARTED")
    print("=" * 50)

    for submission in submissions:

        submission_id = submission["submission_id"]

        print(f"\nEvaluating {submission_id}...")

        try:
            result, raw_response = evaluate_code(
                question=submission["question"],
                code=submission["code"],
                prompt_template=prompt_template
            )

            evaluation = {
                "submission_id": submission_id,
                "question_id": submission["question_id"],
                "generator_model": submission["generator_model"],
                "judge_model": MODEL,
                "prompt_version": "structured_rubric_v1",
                "evaluation": result,
                "raw_response": raw_response,
                "evaluated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "status": "success"
            }

            evaluations.append(evaluation)

            print(
                f"SUCCESS: {submission_id} | "
                f"Overall: {result['overall_score']}/10"
            )

        except Exception as error:

            print(f"FAILED: {submission_id}")
            print(f"Reason: {error}")

            evaluations.append({
                "submission_id": submission_id,
                "judge_model": MODEL,
                "status": "failed",
                "error": str(error)
            })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(evaluations, file, indent=4)

    successful = sum(
        item["status"] == "success"
        for item in evaluations
    )

    print("\n" + "=" * 50)
    print("AI JUDGING COMPLETED")
    print(f"Total submissions: {len(submissions)}")
    print(f"Successful evaluations: {successful}")
    print(f"Failed evaluations: {len(submissions) - successful}")
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
