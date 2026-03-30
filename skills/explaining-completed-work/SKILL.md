---
name: explaining-completed-work
description: Use when a task is complete and the user asks what was done, how it was done, why those choices were made, or wants a Feynman-style walkthrough of the key concepts
---

# Explaining Completed Work

Turn finished work into a clear walkthrough that teaches, not just reports.

## What This Skill Does

Use this skill after a task is done when the user wants a deeper explanation:

- what changed
- how it was done
- why this approach was chosen
- what key concept actually matters
- where the edge cases or boundaries are

The default structure is:

1. Result
2. Mechanism
3. Reason
4. Concept
5. Boundary

## Why This Matters

Many technical explanations fail in one of two ways:

- they are too shallow and only say "I ran these commands"
- they are too abstract and teach concepts without tying them back to the actual work

This skill fixes both problems by teaching from the completed outcome backward. That makes it useful for learning, review, onboarding, and trust-building after implementation or debugging work.

From a learning perspective, this matters because people remember explanations better when they can connect:

- the visible outcome
- the causal steps
- the reason behind the decision
- the concept in plain language

## When to Use

- The task is already complete and the user asks "what did you do?"
- The user asks "how did you do it?" or "why did you do it this way?"
- The user wants a walkthrough after debugging, implementation, research, or operations work
- The user asks for a beginner-friendly or Feynman-style explanation
- The user wants both the practical steps and the underlying concepts

Do not use this for pre-implementation design work or for generic tutorials unrelated to the completed task.

## Core Pattern

Always explain in this order unless the user asks otherwise:

1. **Result**: What changed or what outcome was achieved.
2. **Mechanism**: The concrete steps, commands, files, APIs, or decisions that made it happen.
3. **Reason**: Why this approach was correct or safer than nearby alternatives.
4. **Concept**: The key idea explained in simple language, then one level deeper.
5. **Boundary**: What this did not do, what assumptions mattered, and where confusion usually comes from.

## Quick Reference

| User asks | Response shape |
| --- | --- |
| "What did you do?" | Result + short mechanism |
| "How did you do it?" | Mechanism + concrete example |
| "Why this approach?" | Reason + rejected alternative |
| "What does this concept mean?" | Plain-language concept + analogy + mapping back to the task |
| "Go deeper" | Add one more layer without losing the simple explanation |

## How to Explain

Use this sequence:

1. State the finished outcome in one or two sentences.
2. Name the exact objects involved: files, commands, APIs, settings, or decisions.
3. Explain each step in plain language before using jargon.
4. For each important choice, say why it was chosen and what was avoided.
5. Pick one or two concepts that matter most and teach them with the Feynman method.
6. End with limits, caveats, or common misunderstandings.

For every key concept:

1. Say it in simple words a beginner can follow.
2. Use a concrete analogy or mental model.
3. Map the analogy back to the real task.
4. Name the common wrong intuition.
5. Give the precise version only after the simple version is clear.

## Example

See [examples/audio-extraction-walkthrough.md](examples/audio-extraction-walkthrough.md) for a concrete example based on extracting audio from a video and importing it into the macOS Music app.

## Common Mistakes

- Starting with tool syntax instead of the user-visible result
- Dumping a changelog instead of explaining the causal chain
- Using jargon before defining it
- Explaining only "how" and skipping "why"
- Giving only the simple version and hiding the precise boundary conditions
- Teaching the concept without tying it back to the exact task that was completed

## Red Flags

- "Here are the commands I ran" with no explanation of purpose
- "It just works this way" instead of a reasoned tradeoff
- "Fixed" or "lossless" used loosely when the evidence does not support it
- Three paragraphs of terminology before one sentence of outcome

When these appear, restart from the five-part order: result, mechanism, reason, concept, boundary.
