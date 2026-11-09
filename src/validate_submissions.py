import json
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = ROOT / "data" / "code_submissions.json"


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        submissions = json.load(file)

    print("\nCODE SYNTAX VALIDATION")
    print("=" * 45)

    valid = 0
    invalid = 0

    for submission in submissions:
        code = submission["code"]

        try:
            ast.parse(code)
            print(f'{submission["submission_id"]}: VALID')
            valid += 1

        except SyntaxError as error:
            print(
                f'{submission["submission_id"]}: INVALID - {error}'
            )
            invalid += 1

    print("\nSUMMARY")
    print(f"Valid submissions: {valid}")
    print(f"Invalid submissions: {invalid}")
    print(f"Total submissions: {len(submissions)}")


if __name__ == "__main__":
    main()
