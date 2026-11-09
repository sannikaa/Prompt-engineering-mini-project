import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SUBMISSIONS = ROOT / "data/code_submissions.json"
OUTPUT = ROOT / "data/human_annotations.csv"

import json

with open(SUBMISSIONS, encoding="utf-8") as f:
    submissions = json.load(f)

fields = [
    "submission_id",
    "reviewer_id",
    "correctness",
    "security",
    "readability",
    "efficiency",
    "comments"
]

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for submission in submissions:
        for reviewer in ["R1", "R2", "R3", "R4"]:
            writer.writerow({
                "submission_id": submission["submission_id"],
                "reviewer_id": reviewer,
                "correctness": "",
                "security": "",
                "readability": "",
                "efficiency": "",
                "comments": ""
            })

print("Human annotation template created.")
print("Total reviews:", len(submissions) * 4)
print("File:", OUTPUT)
