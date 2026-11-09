import csv
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "src"))

from judge import evaluate_code, DIMENSIONS


SUBMISSIONS_FILE = ROOT / "data" / "code_submissions.json"

PROMPT_FILES = {
    "zero_shot": ROOT / "prompts" / "zero_shot.txt",
    "few_shot": ROOT / "prompts" / "few_shot.txt",
    "structured_rubric": ROOT / "prompts" / "structured_rubric.txt"
}

RESULTS_FILE = ROOT / "experiments" / "results" / "prompt_benchmark_results.json"
CSV_FILE = ROOT / "experiments" / "results" / "prompt_benchmark_summary.csv"


def main():

    with open(SUBMISSIONS_FILE, encoding="utf-8") as file:
        submissions = json.load(file)

    prompt_templates = {}

    for name, path in PROMPT_FILES.items():
        with open(path, encoding="utf-8") as file:
            prompt_templates[name] = file.read()

    all_results = []

    print("\nPROMPT ENGINEERING BENCHMARK")
    print("=" * 55)

    for prompt_name, template in prompt_templates.items():

        print(f"\nEXPERIMENT: {prompt_name.upper()}")
        print("-" * 45)

        for submission in submissions:

            submission_id = submission["submission_id"]

            print(f"Evaluating {submission_id}...")

            try:
                result, raw_response = evaluate_code(
                    question=submission["question"],
                    code=submission["code"],
                    prompt_template=template
                )

                record = {
                    "submission_id": submission_id,
                    "question_id": submission["question_id"],
                    "prompt_technique": prompt_name,
                    "judge_model": "qwen2.5:7b",
                    "evaluation": result,
                    "raw_response": raw_response,
                    "status": "success",
                    "evaluated_at": datetime.now(
                        timezone.utc
                    ).isoformat()
                }

                print(
                    f"SUCCESS | Overall: "
                    f"{result['overall_score']}/10"
                )

            except Exception as error:

                record = {
                    "submission_id": submission_id,
                    "question_id": submission["question_id"],
                    "prompt_technique": prompt_name,
                    "status": "failed",
                    "error": str(error)
                }

                print(f"FAILED: {error}")

            all_results.append(record)

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump(all_results, file, indent=4)

    # Calculate averages for each prompting technique
    summary = []

    print("\nBENCHMARK SUMMARY")
    print("=" * 55)

    for technique in PROMPT_FILES:

        successful = [
            item for item in all_results
            if item["prompt_technique"] == technique
            and item["status"] == "success"
        ]

        row = {
            "prompt_technique": technique,
            "successful_evaluations": len(successful),
            "failed_evaluations": 10 - len(successful)
        }

        for dimension in DIMENSIONS + ["overall_score"]:

            scores = [
                item["evaluation"][dimension]
                for item in successful
            ]

            average = (
                sum(scores) / len(scores)
                if scores else None
            )

            row[f"average_{dimension}"] = (
                round(average, 2) if average is not None else ""
            )

        summary.append(row)

        print(f"\n{technique}:")
        print(f"Successful: {len(successful)}/10")

        for dimension in DIMENSIONS + ["overall_score"]:
            print(
                f"Average {dimension}: "
                f"{row[f'average_{dimension}']}"
            )

    if summary:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=summary[0].keys()
            )
            writer.writeheader()
            writer.writerows(summary)

    print("\nBENCHMARK COMPLETED")
    print(f"Total evaluations: {len(all_results)}")
    print(f"Results: {RESULTS_FILE}")
    print(f"Summary: {CSV_FILE}")


if __name__ == "__main__":
    main()
