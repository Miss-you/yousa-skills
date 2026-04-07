# README I18n Maintenance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a generated dual-language README workflow with English as the default landing page, then align repository contribution guidance with that workflow.

**Architecture:** Store README-facing skill metadata in a shared manifest, render both root README files from language-specific templates, and update repository agent instructions so future skill submissions regenerate both outputs consistently. Keep the implementation dependency-free and verifiable with standard-library Python tests plus generator check mode.

**Tech Stack:** Markdown, JSON, Python 3 standard library, git worktree workflow

---

### Task 1: Build README generation source and tests

**Files:**
- Create: `docs/readme/skills.json`
- Create: `docs/readme/templates/README.en.md.tmpl`
- Create: `docs/readme/templates/README.zh-CN.md.tmpl`
- Create: `scripts/render_readmes.py`
- Create: `tests/test_render_readmes.py`
- Modify: `README.md`
- Create: `README.zh-CN.md`

**Step 1: Write the failing test**

Create `tests/test_render_readmes.py` covering:
- manifest validation rejects duplicate skill names
- rendering produces a skills table row for a known skill
- installation examples include every skill name
- `--check` mode reports drift when rendered output differs

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_render_readmes.py -v`
Expected: FAIL because `scripts/render_readmes.py` and source files do not exist yet.

**Step 3: Write minimal implementation**

Implement:
- manifest loader and validator
- template renderer with placeholders for skill table and install examples
- README writer and `--check` mode
- initial manifest and both templates
- generated root README outputs

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_render_readmes.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/readme scripts/render_readmes.py tests/test_render_readmes.py README.md README.zh-CN.md
git commit -m "feat: add generated bilingual README workflow"
```

### Task 2: Align repository guidance with the new README workflow

**Files:**
- Modify: `CLAUDE.md`
- Create: `AGENT.md`
- Modify: `.claude/skills/contribute-skill/SKILL.md`

**Step 1: Write the failing test**

Define verification rules in the task itself:
- `CLAUDE.md` must stop instructing contributors to hand-edit only `README.md`
- `AGENT.md` must exist and mirror the new bilingual README maintenance rules
- `.claude/skills/contribute-skill/SKILL.md` must mention manifest updates and regenerating both README files

**Step 2: Run verification to confirm current failure**

Run:

```bash
rg -n "README.md" CLAUDE.md .claude/skills/contribute-skill/SKILL.md
test -f AGENT.md
```

Expected:
- `CLAUDE.md` and `.claude/skills/contribute-skill/SKILL.md` still reference only `README.md`
- `test -f AGENT.md` fails because the file does not exist

**Step 3: Write minimal implementation**

Update repository guidance so all three instruction files point to:
- `docs/readme/skills.json`
- `python3 scripts/render_readmes.py`
- both generated README outputs

**Step 4: Run verification to verify it passes**

Run:

```bash
test -f AGENT.md
rg -n "README.zh-CN.md|docs/readme/skills.json|render_readmes.py" CLAUDE.md AGENT.md .claude/skills/contribute-skill/SKILL.md
```

Expected: PASS with matches in all guidance files

**Step 5: Commit**

```bash
git add CLAUDE.md AGENT.md .claude/skills/contribute-skill/SKILL.md
git commit -m "docs: align contributor guidance with README generation workflow"
```

### Task 3: Review, regenerate, and verify end-to-end

**Files:**
- Review only: repository diff from this branch

**Step 1: Run review checks**

Run:

```bash
python3 -m unittest tests/test_render_readmes.py -v
python3 scripts/render_readmes.py --check
git diff --check
```

Expected:
- tests pass
- README outputs are up to date
- no whitespace or patch formatting issues

**Step 2: Request code review**

Use subagent review on the completed diff for:
- spec compliance against this plan
- code quality and maintenance risks

**Step 3: Fix review findings**

If review finds issues, apply minimal fixes and rerun Step 1.

**Step 4: Final status check**

Run:

```bash
git status --short
```

Expected: only intended tracked changes remain
