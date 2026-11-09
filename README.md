# LLM-as-a-Judge for Automated Code Auditing

## Project overview

This project evaluates whether a large language model (LLM) can act as an automated judge for Python code submissions. The system generates candidate solutions, checks their functional behaviour, evaluates them across multiple quality dimensions, and compares different judging prompts and bias-related conditions.

## Models

- **Code generator:** `qwen2.5-coder:3b` (via Ollama)
- **Code judge:** `qwen2.5:7b` (via Ollama)

## Evaluation dimensions

Each submission is evaluated on a 0–10 scale for:

1. Correctness
2. Security
3. Readability
4. Efficiency

The detailed scoring criteria are in [`documentation/evaluation_rubric.md`](documentation/evaluation_rubric.md).

## Project workflow

1. Generate Python solutions for 10 coding questions.
2. Validate generated submissions.
3. Run functional test cases.
4. Evaluate submissions using the LLM judge.
5. Compare zero-shot, few-shot, and structured-rubric prompting.
6. Run pairwise and bias-oriented experiments.
7. Compare judge scores with the annotation dataset using statistical analysis.
8. Inspect the results in the Streamlit dashboard.

## Main results recorded in this repository

- Functional testing: **40 of 41 tests passed (97.56%)**.
- AI judging: **10 of 10 submissions evaluated successfully**.
- Prompt benchmark: **30 of 30 evaluations completed successfully**.
- Average overall scores in the prompt benchmark:
  - Zero-shot: **9.47/10**
  - Few-shot: **9.50/10**
  - Structured rubric: **9.93/10**
- Self-enhancement experiment: **10 successful comparisons; judge-model-generated code won 3 comparisons**.
- Statistical analysis output: `experiments/results/statistical_analysis.json`.

These are observed outputs from the recorded experiment runs. High judge scores do not, by themselves, establish that the judge is accurate.

## Repository structure

```text
.
├── app/                  # Streamlit dashboard
├── data/                 # Questions, submissions, annotations and evaluations
├── documentation/        # Evaluation rubric and project report
├── experiments/          # Benchmark and bias experiment scripts
│   └── results/          # Saved experiment outputs
├── prompts/              # Prompt templates
├── src/                  # Generation, judging and validation code
├── tests/                # Functional test cases
└── requirements.txt
```

## Setup

This project uses Python and Ollama.

1. Install Python 3.11 or a compatible Python version.
2. Install [Ollama](https://ollama.com/).
3. Pull the models:

```bash
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5:7b
```

4. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

5. Install dependencies:

```bash
pip install -r requirements.txt
```

6. Start the Ollama service if it is not already running.

## Run the dashboard

```bash
streamlit run app/streamlit_app.py
```

Then open the local URL printed in the terminal (usually `http://localhost:8501`).

## Re-running experiments

Run commands from the repository root with the virtual environment activated. Examples:

```bash
python src/functional_validator.py
python src/judge.py
python experiments/prompt_benchmark.py
python experiments/pairwise_evaluation.py
python experiments/position_bias.py
python experiments/verbosity_bias.py
python experiments/self_enhancement_bias.py
python experiments/statistical_analysis.py
```

Some experiments depend on generated input files from earlier steps. Run the corresponding generation scripts first where required.

## Important interpretation notes

- The functional test run recorded 40/41 passing tests. The remaining failure was in Q07: the generated function returned `None` for an input with fewer than two distinct values, while the test expected `ValueError`.
- Q09's recorded functional test output and the inspected implementation appeared inconsistent about support for `()`, `[]`, and `{}`. This discrepancy should be checked before making claims about Q09 correctness.
- Spearman correlation is undefined for dimensions where one set of scores is constant. The statistical script reported this for correctness/security-related inputs as shown in its output.
- The annotation file's reviewer provenance must match the actual data collection process. Do not describe AI-generated or simulated ratings as independent human reviews. If ratings were not collected independently from human reviewers, describe them as AI-assisted/simulated annotations and interpret the human-versus-AI comparison accordingly.

## Limitations

- The experiments use a small set of 10 coding questions and one generator/judge model configuration.
- Very high judge scores may indicate lenient scoring or limited test coverage.
- Functional tests cover only the supplied cases, not every possible input.
- The observed prompt benchmark scores are model-assigned scores; independent validation is needed before concluding that one prompt is objectively more accurate.
- Bias experiments are exploratory and should be interpreted in light of their sample size and experimental design.

## Future work

- Expand the question set and edge-case test coverage.
- Use independent human reviewers and document the annotation protocol.
- Repeat experiments across multiple models and random seeds.
- Add calibration and agreement analysis.
- Investigate the Q07 and Q09 validation issues.
