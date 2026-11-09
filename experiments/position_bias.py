import json
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ORIGINAL = ROOT / "data/code_submissions.json"
ALTERNATIVE = ROOT / "data/alternative_submissions.json"
PROMPT = ROOT / "prompts/pairwise.txt"

OUTPUT = ROOT / "experiments/results/position_bias_results.json"


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

    return result["winner"]


def main():
    original = json.load(open(ORIGINAL, encoding="utf-8"))
    alternative = json.load(open(ALTERNATIVE, encoding="utf-8"))
    template = PROMPT.read_text(encoding="utf-8")

    alt_map = {x["question_id"]: x for x in alternative}
    results = []

    for a in original:
        b = alt_map.get(a["question_id"])

        if not b:
            continue

        print("Testing position bias:", a["question_id"])

        try:
            first = judge(
                a["question"], a["code"], b["code"], template
            )

            reversed_result = judge(
                a["question"], b["code"], a["code"], template
            )

            # Convert reversed positions back to original identities
            reversed_original = {
                "A": "B",
                "B": "A",
                "TIE": "TIE"
            }[reversed_result]

            consistent = first == reversed_original

            results.append({
                "question_id": a["question_id"],
                "original_order_winner": first,
                "reversed_order_winner": reversed_result,
                "reversed_mapped_to_original": reversed_original,
                "position_consistent": consistent,
                "status": "success"
            })

            print("Position consistent:", consistent)

        except Exception as error:
            results.append({
                "question_id": a["question_id"],
                "status": "failed",
                "error": str(error)
            })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    successful = [x for x in results if x["status"] == "success"]

    consistent = sum(x["position_consistent"] for x in successful)

    print("\nPOSITION BIAS RESULTS")
    print("Successful pairs:", len(successful))
    print("Consistent pairs:", consistent)
    print("Inconsistent pairs:", len(successful) - consistent)


if __name__ == "__main__":
    main()
