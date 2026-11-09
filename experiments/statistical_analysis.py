import json
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent

HUMAN_FILE = ROOT / "data/human_annotations.csv"
AI_FILE = ROOT / "data/judge_evaluations.json"

OUTPUT = ROOT / "experiments/results/statistical_analysis.json"

DIMENSIONS = [
    "correctness",
    "security",
    "readability",
    "efficiency"
]


def main():
    human = pd.read_csv(HUMAN_FILE)

    required = [
        "submission_id",
        "reviewer_id"
    ] + DIMENSIONS

    if human[required].isna().any().any():
        raise ValueError(
            "Human annotations are incomplete. "
            "Complete all 40 reviews first."
        )

    for dimension in DIMENSIONS:
        if not human[dimension].between(0, 10).all():
            raise ValueError(
                f"Invalid scores in {dimension}"
            )

    with open(AI_FILE, encoding="utf-8") as f:
        ai_data = json.load(f)

    ai_rows = []

    for item in ai_data:
        if item.get("status") != "success":
            continue

        row = {
            "submission_id": item["submission_id"]
        }

        for dimension in DIMENSIONS:
            row[dimension] = item["evaluation"][dimension]

        ai_rows.append(row)

    ai = pd.DataFrame(ai_rows)

    human_mean = (
        human.groupby("submission_id")[DIMENSIONS]
        .mean()
        .reset_index()
    )

    merged = human_mean.merge(
        ai,
        on="submission_id",
        suffixes=("_human", "_ai")
    )

    results = {
        "number_of_submissions": len(merged),
        "number_of_human_reviews": len(human),
        "dimensions": {}
    }

    for dimension in DIMENSIONS:
        h = merged[f"{dimension}_human"]
        a = merged[f"{dimension}_ai"]

        mae = (h - a).abs().mean()
        correlation, p_value = spearmanr(h, a)

        results["dimensions"][dimension] = {
            "human_average": round(float(h.mean()), 3),
            "ai_average": round(float(a.mean()), 3),
            "mean_absolute_error": round(float(mae), 3),
            "spearman_correlation": (
                round(float(correlation), 3)
                if pd.notna(correlation) else None
            ),
            "p_value": (
                round(float(p_value), 4)
                if pd.notna(p_value) else None
            )
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print("\nHUMAN VS AI ANALYSIS")
    print("=" * 45)

    for dimension, values in results["dimensions"].items():
        print(f"\n{dimension.upper()}")
        for key, value in values.items():
            print(f"{key}: {value}")

    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()
