import json
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ORIGINAL = ROOT / "data/code_submissions.json"
ALTERNATIVE = ROOT / "data/alternative_submissions.json"
PROMPT = ROOT / "prompts/pairwise.txt"

OUTPUT = ROOT / "experiments/results/pairwise_results.json"


def main():
    with open(ORIGINAL, encoding="utf-8") as f:
        original = json.load(f)

    with open(ALTERNATIVE, encoding="utf-8") as f:
        alternative = json.load(f)

    with open(PROMPT, encoding="utf-8") as f:
        template = f.read()

    alt_by_id = {x["question_id"]: x for x in alternative}
    results = []

    for a in original:
        b = alt_by_id.get(a["question_id"])

        if b is None:
            continue

        print("Comparing:", a["question_id"])

        prompt = (
            template
            .replace("{question}", a["question"])
            .replace("{code_a}", a["code"])
            .replace("{code_b}", b["code"])
        )

        try:
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

            results.append({
                "question_id": a["question_id"],
                "program_a": a["submission_id"],
                "program_b": b["submission_id"],
                "result": result,
                "status": "success"
            })

            print("Winner:", result["winner"])

        except Exception as error:
            print("FAILED:", error)

            results.append({
                "question_id": a["question_id"],
                "status": "failed",
                "error": str(error)
            })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print("\nPAIRWISE EVALUATION COMPLETED")
    print("Successful:", sum(x["status"] == "success" for x in results))
    print("Failed:", sum(x["status"] == "failed" for x in results))


if __name__ == "__main__":
    main()
