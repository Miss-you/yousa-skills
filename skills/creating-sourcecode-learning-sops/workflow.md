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
├── principles.md                # Learning & code-reading principles governing the SOP
├── reviews/                     # Subagent review reports, one file per review pass
│   ├── review-feedback-v1.md
│   └── review-feedback-v2.md
├── human-simulation.md          # Junior engineer simulation findings (Step 8)
├── phase1-birdview/             # Phase templates
│   ├── code-map.md
│   └── self-check.md
├── phase2-tracing/
│   └── call-chain.md
├── phase3-tool/
│   ├── deep-dive.md
│   └── experiment.py            # If applicable; use experiment.sh instead only when shell is more appropriate
├── phase4-experiment/
│   └── experiment-log.md
├── phase5-integration/
│   └── architecture-diagram.md
├── final/
│   └── learning-report.md
└── i18n/                        # Step 9 artifacts
    ├── glossary.md              # English → Chinese term mapping
    └── translation-selfcheck.md # Self-check report for bilingual rendering
```

Use `WriteFile` or `Shell` to create these files immediately. Do not wait until the end.

---

## Step 2: Establish Principles

Write `principles.md` (created in Step 1) to govern the SOP design. It must include principles from **both** dimensions:

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
3. Write a structured report to `reviews/review-feedback-v1.md` containing:
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

After fixing, if the number of changes is significant, **run a second subagent review** (v2) to validate the fixes. Write the follow-up report to `reviews/review-feedback-v2.md`.

---

## Step 7: Acceptance Criteria

> **When to run:** this is the **final completion gate**, executed only after Steps 8 and 9 are done. Its numeric position is historical (Steps 1–8 existed before Step 9 was added). Do not open this checklist until human simulation (Step 8) and bilingual rendering (Step 9) are both complete.

Before declaring completion, confirm every checkbox below is true:

- [ ] Workspace `study-{feature}-sop/` exists with all phase directories and templates
- [ ] `README.md` is the single source of truth; a learner can follow it sequentially
- [ ] Every referenced code path (file, class, function, test) was verified by actual execution
- [ ] At least one round of subagent review was performed and its feedback incorporated
- [ ] Learning science principles are explicitly named and visibly embedded in phases
- [ ] At least one runnable experiment script is provided in the workspace
- [ ] Final report template has a clear structure and a self-check quality checklist
- [ ] No broken commands or non-existent file paths remain in the SOP
- [ ] Human simulation report (`human-simulation.md`) has been generated and friction points addressed
- [ ] Step 9 bilingual rendering complete: every target file has English + Chinese paired prose, `i18n/glossary.md` exists, and `i18n/translation-selfcheck.md` shows all checks passed

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

Write your findings to `human-simulation.md` (created in Step 1) as:
- Friction points (ordered by severity)
- Questions that the SOP left unanswered
- Suggested micro-fixes (1-2 sentences each)
```

Apply the micro-fixes that meaningfully reduce friction.

---

## Step 9: Bilingual Rendering (中英双语化)

Only run this step **after** Steps 1–8 are complete and the English SOP is stable. Translation exposes prose ambiguities; doing it earlier forces re-translation.

### 9.1 Scope — What to Translate vs. Preserve

**Translate (prose):**
- Paragraphs, list items, checklist text
- Natural-language cells inside tables
- Explanation/comment text authored by you

**Headings — special case (see 9.3):**
- Headings ARE translated, but use single-line `English · 中文` format (one heading, not two), so TOC and anchor IDs stay stable.

**Preserve byte-identical (do NOT translate):**
- Fenced code blocks (```...```) — including language tag and every character inside
- Inline code (`...`)
- Mermaid, ASCII, or other diagrams
- File paths, shell commands, CLI flags
- Identifiers: class names, function names, test names, variable names
- YAML frontmatter
- URLs and link targets (link text may be translated)

### 9.2 Target Files

Translate **Markdown prose artifacts only**. Never touch executable or non-prose files even if they live in the same phase directory.

Translate (user-facing `.md` artifacts):
- `README.md` (master SOP)
- `principles.md`
- All phase **template `.md` files** under `phase1-*/` through `phase5-*/` (e.g. `code-map.md`, `call-chain.md`, `deep-dive.md`, `experiment-log.md`, `architecture-diagram.md`, `self-check.md`)
- `final/learning-report.md`

Do **not** translate:
- Executable scripts under any phase directory (e.g. `phase3-tool/experiment.py`, `*.sh`) — these are code, covered by 9.1's preservation rule
- `reviews/*.md` (subagent review reports — internal process artifacts)
- `human-simulation.md` (internal)
- `i18n/*.md` (meta-files about translation itself)

### 9.3 Layout Convention — Paragraph Pairing

**Body prose** — render English original first, then a blank line, then the Chinese translation:

```
The entry point receives an inbound event and dispatches to the router.

入口点接收入站事件并分发给路由器。
```

Do not mix inline translations in body prose (e.g. `English (中文)`) — it harms diff and copy-paste.

**Headings — one-line bilingual form** (exception to the rule above):

```
## Phase 1: Birdview · 阶段 1：鸟瞰
```

Rationale: emitting two separate headings (`## Phase 1: Birdview` then `## 阶段 1：鸟瞰`) creates duplicate TOC entries. The `EN · 中文` form keeps a single TOC entry while showing both languages inline.

**Caveat — anchor slugs change.** GitHub-style Markdown derives anchor slugs from the full heading text, so `## Phase 1: Birdview` and `## Phase 1: Birdview · 阶段 1：鸟瞰` produce different slugs. If any external doc, README, or intra-repo link already targets the original English-only anchor, bilingualizing the heading will break that link. Two mitigations:

1. Before translating, grep for `#phase-1-birdview`-style anchor references inside the repo (and any known consumers). If none exist, the slug change is safe.
2. If stable anchors are required, keep the heading English-only and put the Chinese translation on the immediately following non-heading line as body prose, or add an explicit HTML anchor above the heading (e.g. `<a id="phase-1-birdview"></a>`) and point links at the explicit id.

### 9.4 Glossary First

Before translating, create `i18n/glossary.md` with a table of key technical terms discovered during Steps 1–6:

| English | Chinese | Notes |
|---------|---------|-------|
| call chain | 调用链 | |
| entry point | 入口点 | |
| hook | 钩子 | Keep English `hook` inside code refs |

Extend the glossary as you translate. **Rule:** once a term has a Chinese mapping, every later occurrence must use the same mapping.

### 9.5 Batch Strategy

Translate in batches to bound context and preserve structure:

1. **One file at a time.** Never translate multiple files in a single pass.
2. **Within a file, split by `##` heading.** Each H2 section is one batch.
3. For each batch:
   a. Extract prose blocks only; list them with stable IDs (e.g. `P1`, `P2`, ...).
   b. Translate each prose block, consulting `glossary.md`.
   c. Re-inject Chinese paragraphs beneath their English counterparts, preserving surrounding code/diagram/structure exactly.
   d. After re-injection, verify non-prose content (code, diagrams, paths, commands) is unchanged. If `git diff` is available, non-prose lines should show zero changes; otherwise eyeball-scan the batch.

### 9.6 Ambiguity Escape Hatch

Translation often surfaces ambiguity in the original English prose. Track these as you go.

**If you accumulate ≥ 3 original-prose ambiguities during translation, STOP.** Return to Step 6 to fix the English source, then re-run affected batches. Do not ship translations that paper over unclear original prose.

### 9.7 Self-Check (记录到 `i18n/translation-selfcheck.md`)

After all files are translated, run every check below and record results:

- [ ] **Code-block integrity:** For each translated file, visually scan every fenced code block, inline code span, Mermaid/ASCII diagram, file path, and shell command — confirm they read identically to your memory of the original. If `git diff` is available, use it as the authoritative check; if not, reading is sufficient since 9.1's blocklist already prevents mutation at translation time.
- [ ] **Paragraph-count audit:** For each H2 section, number of English prose blocks equals number of Chinese prose blocks.
- [ ] **No monolingual prose sections remain:** For every H2 section that contains at least one prose paragraph, that section must have both English and Chinese. Pure code / command / diagram appendix sections (no prose) are exempt.
- [ ] **Glossary consistency:** Each English term in `glossary.md` maps to exactly one Chinese translation across all files. Sample 3 terms via `grep` to confirm.
- [ ] **Semantic spot-check:** Randomly sample 3 paragraph pairs per file and confirm the Chinese faithfully conveys the English meaning (not literal word-for-word, not paraphrased beyond intent).
- [ ] **Ambiguity log:** If any original-prose ambiguities were found, they are either fixed (Step 6 loop performed) or explicitly logged with rationale for why they were left as-is.

If any checkbox fails, fix and re-check. Only then declare Step 9 complete.

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
