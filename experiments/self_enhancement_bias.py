import json
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CODER = ROOT / "data/code_submissions.json"
JUDGE = ROOT / "data/judge_model_submissions.json"
PROMPT = ROOT / "prompts/pairwise.txt"

OUTPUT = ROOT / "experiments/results/self_enhancement_results.json"


def compare(question, code_a, code_b, template):
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
    coder = json.load(open(CODER, encoding="utf-8"))
    judge = json.load(open(JUDGE, encoding="utf-8"))

    judge_map = {x["question_id"]: x for x in judge}
    template = PROMPT.read_text(encoding="utf-8")

    results = []

    for a in coder:
        b = judge_map.get(a["question_id"])

        if not b:
            continue

        print("Comparing:", a["question_id"])

        try:
            # Judge-generated code is always Program B here.
            result = compare(
                a["question"],
                a["code"],
                b["code"],
                template
            )

            results.append({
                "question_id": a["question_id"],
                "program_a_model": a["generator_model"],
                "program_b_model": b["generator_model"],
                "winner": result["winner"],
                "judge_generated_code_won": result["winner"] == "B",
                "result": result,
                "status": "success"
            })

            print("Winner:", result["winner"])

        except Exception as error:
            results.append({
                "question_id": a["question_id"],
                "status": "failed",
                "error": str(error)
            })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    successful = [x for x in results if x["status"] == "success"]

    wins = sum(x["judge_generated_code_won"] for x in successful)

    print("\nSELF-ENHANCEMENT EXPERIMENT")
    print("Successful comparisons:", len(successful))
    print("Judge-model code wins:", wins)


if __name__ == "__main__":
    main()
