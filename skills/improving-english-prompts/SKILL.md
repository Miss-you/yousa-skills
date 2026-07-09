---
name: improving-english-prompts
description: Use when the user asks to correct English prompts, broken English, typos, grammar, wording, tone, workplace English, business writing, presentation language, or asks for English practice, quizzes, or help expressing ideas clearly in English.
---

# Improving English Prompts

## Overview

Turn rough English into clear workplace English, then make short practice from real mistakes. Preserve meaning first.

## Core Workflow

1. Read for intent, not just grammar. Keep names, files, technical terms, and domain-specific wording intact unless the user asks to translate them.
2. If intent is clear, do not ask for clarification. Give a corrected version and note any assumption.
3. If ambiguous, provide the most likely corrected version and ask one concise question.
4. Match a recovering-intermediate level: practical, concise, not academic.
5. Include a quiz when the user asks to learn/practice or has 3+ recurring error types.

## Response Shape

Use this structure by default:

- **Corrected Prompt**: one polished version ready to send.
- **Simpler Version**: include when the original is very rough or the corrected prompt is long.
- **Corrected Prompts From This Session**: for multiple prompts, use paired lines: `Old: ...` then `Fixed: ...`.
- **What Changed**: 3-6 bullets using `original` -> `corrected` plus a plain-English reason.
- **Practice Quiz**: 3-5 questions from the user's mistakes. No answer key unless requested. End with: "Reply with your answers, and I will check them."

## Correction Priorities

Prefer concise, natural workplace English:

- Expand chat abbreviations: `plz` -> `please`.
- Use exact nouns: `reference file`, `source file`, `target file`, `row`, `column`, `cell`.
- Structure requests as action + source + target + expected output.
- Split run-ons into 2-3 short sentences.
- Prefer natural phrases: `express my idea`, `communicate my idea`, `My English used to be okay`.
- Keep the user's direct tone. Do not add corporate filler.

## Quiz Types

Choose from the mistakes in the user's prompt:

- Articles: `a`, `an`, `the`, or no article
- Countability: `row` vs `rows`, `sentence` vs `sentences`
- Word choice: `fix`, `correct`, `polish`
- Sentence order: request -> context -> expected output
- Rewrite practice: broken request -> clean prompt
- Presentation: `Context`, `Point`, `Reason`, `Ask`

For follow-up answers, mark correct/incorrect, give the corrected sentence, explain once, and add a similar question if needed.

## Example

User: "plz fill the excel, ref doc is A.xlsx. I need two line."

Corrected prompt:

> Please fill in the Excel file using `A.xlsx` as the reference file. I need two rows.

What changed:

- `plz` -> `Please`: full word for work requests.
- `two line` -> `two rows`: spreadsheets use rows.
- `ref doc` -> `reference file`: clearer wording.

Session review format:

Old: plz fill the excel.
Fixed: Please fill in the Excel file.

Practice quiz:

1. Choose the better word: "I need two ___ in the table." `line / rows`
2. Rewrite: "plz check my ppt typo."

Reply with your answers, and I will check them.
