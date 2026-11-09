import ast
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

SUBMISSIONS_FILE = ROOT / "data" / "code_submissions.json"
TEST_CASES_FILE = ROOT / "tests" / "test_cases.json"
OUTPUT_FILE = ROOT / "data" / "functional_test_results.json"


# This code runs each generated function in a separate process.
RUNNER = r'''
import json
import sys

payload = json.load(sys.stdin)
namespace = {"__name__": "__main__"}

try:
    exec(payload["code"], namespace)

    function = namespace[payload["function_name"]]
    result = function(*payload["args"])

    print(json.dumps({
        "status": "success",
        "result": result
    }))

except Exception as error:
    print(json.dumps({
        "status": "error",
        "error_type": type(error).__name__,
        "error_message": str(error)
    }))
'''


def get_function_name(code):
    """Find the first top-level function in generated code."""

    tree = ast.parse(code)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name

    raise ValueError("No function definition found.")


def run_test(code, function_name, test_case):
    """Run one test case with a time limit."""

    payload = {
        "code": code,
        "function_name": function_name,
        "args": test_case["args"]
    }

    try:
        process = subprocess.run(
            [sys.executable, "-I", "-c", RUNNER],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=3
        )

        if process.returncode != 0:
            return {
                "passed": False,
                "reason": process.stderr.strip() or "Process failed"
            }

        result = json.loads(process.stdout.strip())

        expected_exception = test_case.get("expected_exception")

        if expected_exception:
            passed = (
                result["status"] == "error"
                and result.get("error_type") == expected_exception
            )

            return {
                "passed": passed,
                "actual": result,
                "expected_exception": expected_exception
            }

        if result["status"] != "success":
            return {
                "passed": False,
                "actual": result,
                "expected": test_case.get("expected")
            }

        expected = test_case["expected"]
        actual = result["result"]

        # Avoid treating True and 1 as identical results.
        passed = (
            type(actual) == type(expected)
            and actual == expected
        )

        return {
            "passed": passed,
            "actual": actual,
            "expected": expected
        }

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "reason": "Execution timed out after 3 seconds"
        }

    except (ValueError, json.JSONDecodeError) as error:
        return {
            "passed": False,
            "reason": str(error)
        }


def main():
    with open(SUBMISSIONS_FILE, encoding="utf-8") as file:
        submissions = json.load(file)

    with open(TEST_CASES_FILE, encoding="utf-8") as file:
        test_cases = json.load(file)

    all_results = []

    total_passed = 0
    total_failed = 0

    print("\nFUNCTIONAL CORRECTNESS TESTING")
    print("=" * 55)

    for submission in submissions:

        submission_id = submission["submission_id"]
        question_id = submission["question_id"]
        code = submission["code"]

        print(f"\nTesting {submission_id}...")

        try:
            function_name = get_function_name(code)

            cases = test_cases[question_id]

            submission_passed = 0
            submission_failed = 0
            individual_results = []

            for index, case in enumerate(cases, start=1):

                result = run_test(code, function_name, case)

                if result["passed"]:
                    submission_passed += 1
                    total_passed += 1
                    status = "PASS"
                else:
                    submission_failed += 1
                    total_failed += 1
                    status = "FAIL"

                individual_results.append({
                    "test_case": index,
                    "input": case["args"],
                    **result
                })

                print(f"  Test {index}: {status}")

            all_results.append({
                "submission_id": submission_id,
                "question_id": question_id,
                "function_name": function_name,
                "passed": submission_passed,
                "failed": submission_failed,
                "total": len(cases),
                "results": individual_results
            })

        except Exception as error:

            print(f"  ERROR: {error}")

            all_results.append({
                "submission_id": submission_id,
                "question_id": question_id,
                "error": str(error),
                "passed": 0,
                "failed": len(test_cases.get(question_id, [])),
                "total": len(test_cases.get(question_id, []))
            })

            total_failed += len(test_cases.get(question_id, []))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(all_results, file, indent=4)

    total = total_passed + total_failed
    accuracy = (total_passed / total * 100) if total else 0

    print("\n" + "=" * 55)
    print("FUNCTIONAL TESTING COMPLETED")
    print(f"Total tests: {total}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Pass percentage: {accuracy:.2f}%")
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
