---
description: Fortify — full protection assessment and tiered plan, written to protection-assessment.md
argument-hint: "[path] [notes about the product]"
---
Use the **Fortify** skill in **audit** mode on the current project (or the path given in `$ARGUMENTS`).
Treat any other text in the arguments as context about the product, its crown jewels or its threats.

Follow the skill's Steps 1–5 exactly:
1. Intake — read the codebase first; ask at most 3–4 questions only for what the code can't tell you.
2. Scan — run the skill's scanner and confirm each finding in the code.
3. Assess the five clone vectors and the moat.
4. Build the tiered plan (quick wins, core, advanced), architecture first, honest about limits.
5. Write `protection-assessment.md` in the project root using the report template, in the user's language,
   with every recommendation numbered.

Do not change any code or configuration in this mode. Finish by summarising the top three actions in chat
and asking which numbered items to apply with `/fortify:harden`.
