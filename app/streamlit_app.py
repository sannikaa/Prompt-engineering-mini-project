import json
from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "experiments" / "results"

st.set_page_config(
    page_title="AI Code Auditor",
    page_icon="🔍",
    layout="wide"
)


def load_json(path):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


submissions = load_json(DATA / "code_submissions.json")
evaluations = load_json(DATA / "judge_evaluations.json")
functional = load_json(DATA / "functional_test_results.json")
benchmark = load_json(
    RESULTS / "prompt_benchmark_results.json"
)
pairwise = load_json(RESULTS / "pairwise_results.json")
human = pd.read_csv(DATA / "human_annotations.csv") if (
    DATA / "human_annotations.csv"
).exists() else pd.DataFrame()

st.title("🔍 LLM-as-a-Judge: AI Code Auditor")

st.write(
    "An experimental platform for evaluating AI-generated "
    "Python code using large language models."
)

st.divider()

successful_evaluations = [
    x for x in evaluations if x.get("status") == "success"
]

total_tests = sum(x.get("total", 0) for x in functional)
passed_tests = sum(x.get("passed", 0) for x in functional)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Code submissions", len(submissions))
c2.metric("AI evaluations", len(successful_evaluations))
c3.metric("Functional tests", total_tests)
c4.metric(
    "Tests passed",
    f"{passed_tests}/{total_tests}"
)

st.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Code Evaluation",
        "Prompt Benchmark",
        "Pairwise Comparison",
        "Human Evaluation"
    ]
)

if page == "Overview":

    st.header("Project Overview")

    st.write("""
    This project investigates the use of LLMs as automated
    code judges and studies how prompt design influences
    evaluation quality and consistency.
    """)

    st.subheader("Research dimensions")

    st.write(
        "Correctness · Security · Readability · Efficiency"
    )

    if evaluations:
        scores = []

        for item in successful_evaluations:
            scores.append({
                "Submission": item["submission_id"],
                "Overall Score": item["evaluation"]["overall_score"]
            })

        st.dataframe(pd.DataFrame(scores), width="stretch")

elif page == "Code Evaluation":

    st.header("Individual Code Evaluation")

    ids = [x["submission_id"] for x in submissions]

    selected = st.selectbox("Select submission", ids)

    code = next(
        x for x in submissions
        if x["submission_id"] == selected
    )

    st.subheader(code["question"])
    st.code(code["code"], language="python")

    evaluation = next(
        (
            x for x in successful_evaluations
            if x["submission_id"] == selected
        ),
        None
    )

    if evaluation:
        result = evaluation["evaluation"]

        st.subheader("AI Judge Scores")

        cols = st.columns(4)

        dimensions = [
            "correctness",
            "security",
            "readability",
            "efficiency"
        ]

        for col, dimension in zip(cols, dimensions):
            col.metric(
                dimension.title(),
                f"{result[dimension]}/10"
            )

        st.metric("Overall score", result["overall_score"])

        st.json(result)

    test = next(
        (
            x for x in functional
            if x["submission_id"] == selected
        ),
        None
    )

    if test:
        st.subheader("Functional Test Results")
        st.write(
            f"Passed: {test['passed']} | Failed: {test['failed']}"
        )
        st.json(test.get("results", []))

elif page == "Prompt Benchmark":

    st.header("Prompt Engineering Benchmark")

    path = RESULTS / "prompt_benchmark_summary.csv"

    if path.exists():
        df = pd.read_csv(path)

        st.dataframe(df, width="stretch")

        score_columns = [
            "average_overall_score"
        ]

        chart = df.set_index("prompt_technique")[score_columns]

        st.bar_chart(chart)

    else:
        st.info("Run the prompt benchmark first.")

elif page == "Pairwise Comparison":

    st.header("Pairwise Evaluation")

    successful = [
        x for x in pairwise
        if x.get("status") == "success"
    ]

    if successful:
        rows = []

        for item in successful:
            rows.append({
                "Question": item["question_id"],
                "Winner": item["result"]["winner"],
                "Reason": item["result"].get("reason", "")
            })

        st.dataframe(pd.DataFrame(rows), width="stretch")

    else:
        st.info("Pairwise results are not available yet.")

elif page == "Human Evaluation":

    st.header("Human Evaluation")

    if not human.empty:
        st.dataframe(human, width="stretch")

        if "correctness" in human.columns:
            st.write("Human review statistics")
            st.write(human.describe())

    st.info(
        "Complete the human annotation CSV before "
        "running the final agreement analysis."
    )


st.divider()

st.caption(
    "Academic research prototype | "
    "LLM-as-a-Judge for Automated Code Auditing"
)
