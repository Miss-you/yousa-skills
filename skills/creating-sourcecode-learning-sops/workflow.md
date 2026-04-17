# Creating Sourcecode Learning SOPs — Detailed Workflow

This document provides the step-by-step execution guide for the `creating-sourcecode-learning-sops` skill.

---

## Step 0: Understand the Goal

Before creating anything, confirm with the user (or infer from context):
- **Repository root path**
- **Target feature / module / mechanism name**
- **Desired output location** (default: a new `study-{feature}-sop/` directory inside the repo)
- **Depth expectation** (quick overview vs. deep-dive suitable for onboarding)

If any of these are unclear, ask the user before proceeding.

---

## Step 1: Create Workspace

Create a dedicated workspace with this structure:

```
study-{feature}-sop/
├── README.md                    # The master SOP
├── review-feedback.md           # Subagent review reports (v1, v2, ...)
├── phase1-birdview/             # Phase templates
│   ├── code-map.md
│   └── self-check.md
├── phase2-tracing/
│   └── call-chain.md
├── phase3-tool/
│   ├── deep-dive.md
│   └── experiment.{py,sh}       # If applicable
├── phase4-experiment/
│   └── experiment-log.md
├── phase5-integration/
│   └── architecture-diagram.md
└── final/
    └── learning-report.md
```

Use `WriteFile` or `Shell` to create these files immediately. Do not wait until the end.

---

## Step 2: Establish Principles

Write a `principles.md` (or embed in `README.md`) that governs the SOP design. It must include principles from **both** dimensions:

### Human Learning Science

| Principle | How to embed in the SOP |
|-----------|------------------------|
| **PBL (Project-Based Learning)** | Final deliverable is a shareable learning report, not just notes |
| **Feynman Technique** | Each phase ends with "Explain this to a junior engineer in 3 sentences" |
| **Active Recall** | Each phase has a closed-book self-check quiz before proceeding |
| **Spaced Repetition** | Each new phase begins with a 3-question review of the previous phase |
| **Rubber Duck Debugging** | At least one phase requires speaking/recording an explanation |
| **Cognitive Load Theory** | No phase should exceed 90 minutes of focused work |

### Programmer Code Reading Best Practices

| Principle | How to embed in the SOP |
|-----------|------------------------|
| **MRE (Minimum Reproducible Example)** | Provide runnable tests/scripts that isolate the feature |
| **Call-Chain First** | Before reading internals, trace the entry-to-exit path |
| **Shared vs. Independent** | Explicitly annotate which runtime/state objects are shared |
| **Delete Test** | Ask "If we delete this file/class, what breaks?" |
| **Runtime Verification** | Every referenced test name, file path, and function signature must be verifiable |

---

## Step 3: Generate SOP Draft

Write `README.md` with the following sections:

1. **Learning Goal** — one sentence
2. **Principles** — summary of Step 2
3. **Environment Check** — commands to verify the repo builds/tests run
4. **Phase 1: Birdview** (~30 min) — code map, core files list, 3 closed-book questions
5. **Phase 2: Tracing** (~1h) — follow the call chain from entry to exit
6. **Phase 3: Tool/Module Deep Dive** (~1h) — field analysis, design decisions, runnable experiments
7. **Phase 4: Experimentation** (~1-1.5h) — 3+ safe experiments (print debugging, param validation, prompt mutation)
8. **Phase 5: Integration** (~45 min) — architecture diagram, shared-vs-independent annotations
9. **Final Report** — structured template with quality checklist
10. **Timeline** — suggested session splits (e.g., 3 sessions of ~1.5h)
11. **Appendix** — quick command reference

**Template files must be real files**, not hypothetical. Fill them with scaffold content (headings, empty tables, TODO comments) so the learner only has to fill in answers.

---

## Step 4: Verify Against Code

**This step is mandatory.** Do not skip.

For every code reference in `README.md` and templates, run an actual command to verify it exists and matches:

```bash
# Example verification commands
grep -n "class TargetClass" src/path/to/file.py
rg "def target_function" src/path/
uv run pytest tests/path/test_feature.py::test_specific_case -v --no-header -q
uv run python -c "from module import Class; print(Class)"
```

If a test name does not exist, find the real one via `--collect-only`.
If a function was moved, correct the path.
If a command fails, fix the SOP or add a caveat.

Document the verification results in a private scratchpad or directly fix the SOP.

---

## Step 5: Subagent Review

Dispatch a review subagent with this prompt template:

```
You are a senior engineering learning coach and codebase expert.
Review the following Sourcecode Learning SOP for accuracy and pedagogical quality.

SOP Location: {path_to_README.md}
Codebase Root: {repo_root}
Target Feature: {feature_name}

Review dimensions:
A. Learning Science — Are PBL, Feynman, Active Recall, Spaced Repetition properly embedded? Are time estimates reasonable?
B. Code Accuracy — Does every file path, class name, function name, and test name match the actual codebase?
C. Executability — Can a junior engineer follow this without getting stuck? Are experiments safe to run?
D. Depth — Are hook mechanisms, event forwarding, state management, and error handling covered if they are core to the feature?

Actions required:
1. Read the SOP and all template files.
2. Run verification commands for any suspicious references.
3. Write a structured report to {path_to_review-feedback.md} containing:
   - Overall rating (1-5 stars) and one-sentence summary
   - Issues table: Severity [critical/warning/nice-to-have] | Description | Fix suggestion | Location
   - List of any factual errors found (wrong paths, non-existent tests)
   - Top 3 prioritized improvement recommendations
   - Any particularly strong aspects (so we preserve them)
```

**Important:** The subagent must actually run commands, not just read files.

---

## Step 6: Fix Issues

Read the subagent's review report.

For every **critical** and **warning** item:
- Fix the SOP or template
- Re-run the relevant verification command to confirm the fix
- If the fix changes a code reference, re-verify it against the codebase

For **nice-to-have** items, apply the ones that clearly improve quality; skip the marginal ones.

After fixing, if the number of changes is significant, **run a second subagent review** (v2) to validate the fixes. Update the review report filename (e.g., `review-v2-report.md`).

---

## Step 7: Acceptance Criteria

Before declaring completion, confirm every checkbox below is true:

- [ ] Workspace `study-{feature}-sop/` exists with all phase directories and templates
- [ ] `README.md` is the single source of truth; a learner can follow it sequentially
- [ ] Every referenced code path (file, class, function, test) was verified by actual execution
- [ ] At least one round of subagent review was performed and its feedback incorporated
- [ ] Learning science principles are explicitly named and visibly embedded in phases
- [ ] At least one runnable experiment script is provided in the workspace
- [ ] Final report template has a clear structure and a self-check quality checklist
- [ ] No broken commands or non-existent file paths remain in the SOP

If any checkbox is unchecked, go back to the relevant step.

---

## Step 8: Human Simulation

Dispatch a final validation subagent to simulate a junior engineer:

```
You are a junior engineer who has never read this codebase before.
Your task is to follow the Sourcecode Learning SOP located at {path_to_README.md}.

Do NOT actually spend hours reading code. Instead, simulate the experience:
1. Walk through each phase and identify where you would get stuck, confused, or need more detail.
2. Check if templates are too blank ("blank page fear") or too restrictive.
3. Verify that experiments can be copy-pasted and run without hidden dependencies.
4. Flag any jargon that isn't explained or any command that assumes unstated context.

Write your findings to {path_to_human-simulation.md} as:
- Friction points (ordered by severity)
- Questions that the SOP left unanswered
- Suggested micro-fixes (1-2 sentences each)
```

Apply the micro-fixes that meaningfully reduce friction.

---

## Example Reference

A real-world execution of this workflow can be found at:
`{some_repo}/study-subagent-sop/`

It covers the `kimi-cli` subagent mechanism and includes:
- 5 learning phases
- 2 rounds of subagent review (v1 → v2 → final patch)
- runnable experiment scripts (`validate_params.py`, `exp-c-starter.py`)
- a final report template

Use it as a benchmark for quality and structure.
