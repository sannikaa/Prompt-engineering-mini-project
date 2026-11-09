import json
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INPUT = ROOT / "data/code_submissions.json"
PROMPT = ROOT / "prompts/pairwise.txt"

OUTPUT = ROOT / "experiments/results/verbosity_bias_results.json"


def add_comments(code):
    comments = [
        "# Detailed implementation with explanatory comments.",
        "# The following function solves the specified programming problem.",
        "# Input validation and edge cases are handled by the implementation.",
        "# The implementation follows the required Python logic.",
        "# The return statement provides the computed result."
    ]

    return "\n".join(comments) + "\n\n" + code


def judge(question, code_a, code_b, template):
    prompt = (
        template.replace("{question}", question)
        .replace("{code_a}", code_a)
        .replace("{code_b}", code_b)
    )

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:7b",
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0}
        },
        timeout=600
    )

    response.raise_for_status()

    result = json.loads(response.json()["response"])

    if result.get("winner") not in ["A", "B", "TIE"]:
        raise ValueError("Invalid winner")

    return result


def main():
    submissions = json.load(open(INPUT, encoding="utf-8"))
    template = PROMPT.read_text(encoding="utf-8")

    results = []

    for item in submissions:
        print("Testing verbosity:", item["question_id"])

        verbose_code = add_comments(item["code"])

        try:
            result = judge(
                item["question"],
                item["code"],
                verbose_code,
                template
            )

            results.append({
                "question_id": item["question_id"],
                "program_a": "Original",
                "program_b": "Comment-enhanced",
                "original_code_length": len(item["code"]),
                "verbose_code_length": len(verbose_code),
                "result": result,
                "status": "success"
            })

            print("Winner:", result["winner"])

        except Exception as error:
            results.append({
                "question_id": item["question_id"],
                "status": "failed",
                "error": str(error)
            })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print("\nVERBOSITY EXPERIMENT COMPLETED")
    print("Successful:", sum(x["status"] == "success" for x in results))


if __name__ == "__main__":
    main()
