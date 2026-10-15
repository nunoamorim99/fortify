# Report template — `protection-assessment.md`

Write in the user's language. Keep it readable by a non-specialist: explain each technical term once (glossary at the end). Be concrete to *their* product; delete sections that don't apply.

---

# Protection assessment — {Product name}

*Date · Assessed by Claude with the Fortify skill · Based on: {codebase scan / description only}*

## 1. Executive summary

- **Overall exposure:** {Low / Medium / High / Critical} — one sentence why.
- **The biggest risk:** {one sentence}.
- **The three things to do first:** {bulleted, each one line}.
- **What protection can and can't do here:** {two sentences of honest expectation-setting}.

## 2. What we assessed

- Product and how it reaches users: …
- Crown jewels (what would hurt to lose): …
- Threats considered: …
- Assumptions made (if the user didn't answer): …
- Stack detected: …

## 3. Exposure by clone vector

| Vector | Risk | Why |
|---|---|---|
| Code extraction | | |
| Behavioural cloning | | |
| Data & API harvesting | | |
| Piracy & tampering | | |
| Secret & asset leakage | | |

## 4. Confirmed findings

For each finding: **Severity** · **Where** (file:line) · **What it means in plain words** · **Fix**.
Mask any secret (first 4 characters + `…`). Mark any exposed secret as **rotate now**.

## 5. Protection plan

### Tier 1 — Quick wins (hours, free)
| # | What | Why (vector/finding) | How | Effort | How much it helps |
|---|---|---|---|---|---|

### Tier 2 — Core protection (days)
| # | What | Why | How | Cost / trade-off | How much it helps |
|---|---|---|---|---|---|

### Tier 3 — Advanced (only if justified)
| # | What | Why | How | Cost / trade-off | How much it helps |
|---|---|---|---|---|---|

## 6. Legal & business protection

General information, not legal advice. Trademark, terms of service, trade secrets, database right, patents (if relevant), takedown routes, evidence of authorship.

## 7. Your moat — what a clone can't copy

What already protects the product beyond code, and where to invest so that even a perfect clone loses.

## 8. Next steps

Ordered checklist. Offer to implement Tier 1 now.

## 9. Glossary

Only the terms used in this report, one line each.
