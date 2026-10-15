---
description: Fortify — quick read-only scan for what makes this product easy to copy, crack or scrape
argument-hint: "[path]"
allowed-tools: Read, Glob, Grep, Bash(python3:*), Bash(python:*)
---
Use the **Fortify** skill in **scan** mode on the project at `$ARGUMENTS` (default: the current project root).

Run the skill's scanner (`scripts/scan.py` in the Fortify skill folder) against that path, writing the JSON
to a temporary location, never into the project. Open each flagged file and confirm the finding before
mentioning it; drop anything that turns out to be a false alarm.

Then reply in chat, in plain language, with:
1. The stack detected and an overall exposure level (code-level only).
2. The confirmed findings, most serious first: what each one means for a non-specialist and the fix.
   Mask any secret (first 4 characters only) and mark exposed secrets as **rotate now**.
3. The three fixes to do first.
4. One line noting that a scan can't measure behavioural cloning or the business moat — `/fortify:audit` covers those.

This mode is read-only: do not modify any file.
