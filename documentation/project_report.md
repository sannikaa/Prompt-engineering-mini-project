# Project Report: Evaluative Benchmarking of LLM-as-a-Judge for Automated Code Auditing

## Abstract

This project explores the use of a large language model (LLM) as an automated judge for Python code submissions. A code-generation model produces solutions for a set of programming questions, and a separate LLM evaluates those solutions across correctness, security, readability, and efficiency. The project also compares prompting strategies and explores potential judging biases. The recorded experiments demonstrate a working evaluation pipeline, while also exposing limitations in score calibration, functional-test coverage, and annotation methodology.

## 1. Introduction

Reviewing code manually can require significant time and consistent expertise. An LLM-as-a-Judge approach attempts to automate part of this process by asking a model to assess submissions against explicit criteria. However, an LLM score should not automatically be treated as objective ground truth. The judge may overlook functional defects, assign overly generous scores, or be affected by prompt design and presentation.

The objective of this project is to implement and evaluate an LLM-based code-auditing workflow and examine how its outputs change under different prompting and comparison conditions.

## 2. System and methodology

### 2.1 Models

The recorded setup uses Ollama with:
- Code generator: `qwen2.5-coder:3b`
- Evaluation judge: `qwen2.5:7b`

### 2.2 Dataset

The project contains 10 Python coding questions, covering tasks such as factorial, primality testing, string reversal, palindrome checking, maximum-element selection, duplicate removal, second-largest distinct value, binary search, balanced parentheses, and GCD.

The generator creates a solution for each question. The resulting submissions are stored in `data/code_submissions.json`.

### 2.3 Evaluation dimensions

The judge assigns scores from 0 to 10 for:
- **Correctness:** whether the implementation meets the problem requirements.
- **Security:** whether the implementation avoids unsafe practices.
- **Readability:** whether the implementation is understandable and maintainable.
- **Efficiency:** whether the implementation uses reasonable time and space resources.

The scoring rubric is stored in `documentation/evaluation_rubric.md`.

### 2.4 Functional validation

Generated submissions are checked using the project's functional test harness. The recorded run reported:
- Total tests: 41
- Passed: 40
- Failed: 1
- Pass percentage: 97.56%

The failed Q07 case concerns an input with fewer than two distinct values. The generated implementation returned `None`, whereas the test expected a `ValueError`. This is a specification/implementation mismatch that should be resolved explicitly rather than hidden.

A separate review raised a possible inconsistency for Q09: the inspected implementation appeared to check round parentheses only, while the functional test output reported all Q09 cases passing. The validator and exact executed code should be inspected before drawing a conclusion.

### 2.5 AI judging

The judge successfully evaluated all 10 recorded submissions. The terminal output showed an overall score of 9.25/10 for Q02 and 10/10 for the other nine submissions.

This result indicates that the pipeline completed, but it does not prove that the scores are calibrated or correct. In particular, the Q07 functional failure despite a 10/10 judge score illustrates why external validation is necessary.

## 3. Prompt engineering benchmark

Three prompting strategies were compared on the same 10 submissions:
1. Zero-shot prompting
2. Few-shot prompting
3. Structured-rubric prompting

All 30 evaluations completed successfully. The recorded average overall scores were:

| Prompt strategy | Average overall score |
|---|---:|
| Zero-shot | 9.47/10 |
| Few-shot | 9.50/10 |
| Structured rubric | 9.93/10 |

The structured-rubric prompt produced the highest average judge-assigned score in this run. The difference is descriptive: because the values are scores assigned by the same judging model, they do not independently establish that the structured rubric is more accurate. Independent reference ratings and repeated trials are needed for that conclusion.

## 4. Bias-oriented experiments

The repository includes experiments for pairwise comparison, position bias, verbosity bias, and self-enhancement bias.

The recorded self-enhancement experiment completed 10 comparisons. Judge-model-generated code won 3 comparisons. This is an exploratory observation, not proof that the judge systematically favours its own model family. The model configurations and comparison design should be considered when interpreting the result.

Detailed outputs are stored under `experiments/results/`. The exact result files should be consulted when reporting numerical outcomes for pairwise, position, and verbosity experiments; no additional numerical claims are made here.

## 5. Annotation and statistical comparison

The project includes an annotation dataset and a statistical analysis script that compares annotation scores with AI judge scores. The recorded statistical output was:

| Dimension | Annotation average | AI average | Mean absolute error | Spearman correlation | p-value |
|---|---:|---:|---:|---:|---:|
| Correctness | 9.00 | 10.00 | 1.000 | Undefined | Undefined |
| Security | 10.00 | 10.00 | 0.000 | Undefined | Undefined |
| Readability | 9.45 | 9.90 | 0.525 | 0.124 | 0.7324 |
| Efficiency | 9.50 | 9.80 | 0.575 | 0.373 | 0.2889 |

Spearman correlation is undefined when one of the compared score arrays is constant. The readability and efficiency correlations are weak and their p-values exceed 0.05; these results do not provide statistically significant evidence of rank agreement.

**Annotation provenance must be described accurately in the submitted report.** Only call these ratings human reviews if they were independently provided by actual human reviewers. If they were generated or substantially prepared by an AI system, identify them as AI-assisted or simulated annotations. In that case, the comparison is not an independent human-versus-AI validation and should be interpreted as a pipeline demonstration rather than evidence of agreement with human judgment.

## 6. Dashboard

A Streamlit dashboard is provided in `app/streamlit_app.py`. It is intended to present the evaluation workflow and saved results, including code evaluation, prompt benchmarking, pairwise comparisons, and annotation comparisons.

To launch it:

```bash
streamlit run app/streamlit_app.py
```

The dashboard should be checked locally to ensure each page loads the current result files and does not display stale or missing data.

## 7. Discussion

The experiments show that an LLM judge can be integrated into a repeatable code-evaluation pipeline and can produce structured scores across multiple dimensions. The structured-rubric prompt received the highest average score in the recorded benchmark.

However, the results also show why LLM judging cannot be used as the sole correctness authority. The Q07 mismatch was detected by functional testing but not reflected in the judge's perfect score. High average scores may also indicate leniency or insufficiently discriminating prompts. The constant security scores prevent correlation analysis for that dimension, and the small dataset limits generalization.

## 8. Limitations

1. Only 10 coding questions were evaluated.
2. The results are based on one recorded generator/judge configuration.
3. Functional tests cover selected cases rather than the full input space.
4. The Q07 mismatch and Q09 validator discrepancy require explicit resolution.
5. Constant scores make some correlation statistics undefined.
6. Small sample sizes limit statistical power.
7. Annotation provenance and independence must be documented accurately.
8. The self-enhancement result is exploratory and does not establish a general bias.

## 9. Future work

- Increase the number and diversity of coding questions.
- Add boundary, malformed-input, and adversarial test cases.
- Use independent human reviewers with a documented review protocol.
- Repeat prompt comparisons over multiple runs and models.
- Measure inter-rater agreement and judge calibration.
- Investigate position and verbosity effects with counterbalanced trials.
- Resolve validator inconsistencies and report all failures transparently.

## 10. Conclusion

This project implemented an end-to-end prototype for automated code auditing using an LLM as a judge. It generated code for 10 programming questions, completed 41 functional tests with 40 passes, evaluated all 10 submissions using an LLM judge, and compared three prompting strategies over 30 evaluations. The structured-rubric strategy received the highest average judge score in the recorded run.

The findings support the feasibility of an LLM-assisted code-review pipeline, but they do not establish that LLM scores can replace functional tests or independent human review. Reliable deployment would require broader test coverage, independent annotations, repeated experiments, and careful calibration of judge scores.
