---
name: creating-sourcecode-learning-sops
description: Use when asked to help learn a specific feature in a codebase and produce a guided self-study document or SOP. Triggered by requests like "帮我设计一个学习源码的文档", "如何系统学习这段代码", "生成一份源码阅读指南", or when the goal is to create a reproducible learning workflow for a repository feature.
---

# Creating Sourcecode Learning SOPs

## Overview

When a user wants to systematically learn a specific feature in a codebase, do NOT just read files and return a summary. Instead, create a **verified, multi-phase Study Operating Procedure (SOP)** that combines human learning science with hands-on code verification.

**Core principle:** A good learning SOP must be executable, experiment-driven, and validated against the actual codebase — not just theoretically correct.

## When to Use

- User asks to "系统学习某段代码" or "设计源码阅读流程"
- User wants a reproducible document to study a repo feature independently
- The target involves non-trivial code paths (multiple files, runtime behavior, state machines)
- The output needs to be shareable with other engineers

## When NOT to Use

- The request is just a quick lookup of one function or file
- The user only wants a high-level architecture overview without exercises
- The feature is purely configuration or documentation with no executable code paths

## Core Workflow

Always follow these 8 steps in order:

1. **Create Workspace** — `study-{feature}-sop/` with subdirectories for each phase and final report
2. **Establish Principles** — Write down the human learning + programmer code-reading principles that will govern the SOP design
3. **Generate SOP Draft** — Write `README.md` (the master SOP) and fill-in-the-blank templates for each learning phase
4. **Verify Against Code** — Run actual commands (`pytest`, `grep`, `rg`, `python`) to validate every file path, test name, and function signature referenced in the SOP
5. **Subagent Review** — Dispatch a review subagent to audit the SOP from multiple dimensions (learning science, code accuracy, executability, depth)
6. **Fix Issues** — Address every critical/warning found in the review; re-verify changed facts against the codebase
7. **Acceptance Criteria** — Confirm the SOP meets the quality checklist before finishing
8. **Human Simulation** — Have a subagent simulate a junior engineer following the SOP to surface remaining friction

**REQUIRED:** For the full step-by-step instructions, subagent prompts, and acceptance checklist, read `workflow.md` in this skill directory.

## Acceptance Criteria (Final SOP Must Have)

- [ ] A dedicated workspace with phase-based directories and templates
- [ ] Every referenced code path verified by actual tool execution
- [ ] At least one round of subagent review with structured feedback incorporated
- [ ] Human learning principles explicitly embedded (active recall, Feynman technique, MRE)
- [ ] Executable experiments/scripts that the learner can run safely
- [ ] A final report template with clear structure and quality checklist

## Common Mistakes

- **Writing a narrative instead of an SOP** — learners need phases, outputs, and checklists, not stories
- **Skipping code verification** — file paths and test names drift; always run `grep`/`pytest` to confirm
- **One-shot generation** — without subagent review, subtle inaccuracies (wrong function locations, outdated test names) remain hidden
- **Missing experiments** — purely reading is passive; every SOP must include runnable experiments
