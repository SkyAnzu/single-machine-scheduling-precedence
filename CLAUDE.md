# CLAUDE.md

Repository note:
- This file is a generic editing guide.
- For repository-specific research protocol, defer to `AGENTS.md` and `docs/research/`.
- In particular, dataset lane separation, objective-consistency checks, and evidence standards are defined there and take priority over this generic note.

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Do not assume. Do not hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them instead of picking silently.
- If a simpler approach exists, say so.
- If something is unclear, stop and name the uncertainty.

## 2. Simplicity First

**Use the minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No configurability that was not requested.
- No error handling for impossible scenarios.
- If 200 lines could be 50, simplify.

Ask yourself: would a senior engineer call this overcomplicated? If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Do not improve adjacent code, comments, or formatting without need.
- Do not refactor things that are not part of the task.
- Match the local style.
- If you notice unrelated dead code, mention it instead of deleting it.

When your changes create orphans:
- Remove imports, variables, or functions that your own changes made unused.
- Do not remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the task.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- `Add validation` -> `Write tests for invalid inputs, then make them pass`
- `Fix the bug` -> `Write a test that reproduces it, then make it pass`
- `Refactor X` -> `Ensure tests pass before and after`

For multi-step tasks, state a brief plan:

```text
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria enable independent iteration. Weak criteria such as `make it work` force avoidable guesswork.

---

**These guidelines are working if:** fewer unnecessary changes appear in diffs, fewer rewrites are needed due to overcomplication, and clarifying questions happen before implementation rather than after mistakes.
