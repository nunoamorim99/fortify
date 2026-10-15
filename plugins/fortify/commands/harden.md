---
description: Fortify — apply chosen protections from the assessment, one reviewable change at a time
argument-hint: "[item numbers, e.g. T1-1 T1-3 T2-2 | all-tier1]"
---
Use the **Fortify** skill in **harden** mode on the current project.

Items to apply: $ARGUMENTS

- If `protection-assessment.md` doesn't exist, run the audit first and stop to let the user choose items.
- If no items were given, list the report's recommendations by number and ask which to apply.
  `all-tier1` means every Tier 1 item.

Follow the skill's Step 6: implement each chosen item as a small, explained change; run the build and
tests after each one; watch for breakage from minification and obfuscation (reflection, serialisation,
dynamic imports, crash symbolication); never commit secrets; tell the user to rotate any secret that was
moved out of the client. Never add code that harms users or attackers' machines.

When done, re-run the scanner, show the before/after, and mark the applied items as done in
`protection-assessment.md`.
