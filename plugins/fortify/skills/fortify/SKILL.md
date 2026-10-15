---
name: fortify
description: Assess how easily a software product can be reverse engineered, cracked, scraped or cloned, then propose and implement a tailored protection plan in plain language. Use when someone wants to protect their app, game, SaaS, API, data or AI product from copying, piracy or reverse engineering, asks about obfuscation, anti-tamper, licensing or clone prevention, or runs /fortify.
---

# Fortify

Help a developer or product owner understand how exposed their product is to copying, and what to do about it — explained so that someone who has never heard the word "obfuscation" can follow and decide.

## Principles (read first)

1. **Honesty over reassurance.** Nothing that runs on a machine the attacker controls can be made impossible to reverse engineer. Protection raises the cost and time of copying; it never makes it zero. Never promise "uncrackable" or "unclonable". Say how much harder each measure makes things and against whom.
2. **Code is rarely the real target anymore.** With AI, many clones are rebuilt from *observed behaviour*, public docs and screenshots (clean-room), without touching the code. Code hardening does nothing against that. Always assess behavioural cloning and the business moat, not only the binary.
3. **Architecture beats tricks.** The strongest protection is not shipping the valuable part: keep it on a server behind authentication. Recommend this first whenever it fits.
4. **Protect the user's own product only.** This skill is defensive. If the request is to crack, bypass or copy someone else's product, decline that part and offer to assess the user's own product instead.
5. **Plain language.** Every technical term gets a one-line explanation the first time it appears (see `references/glossary.md`). Assume the reader is smart but not a security specialist.
6. **Proportionality.** A side project does not need Denuvo. Match cost, effort and performance impact to what is actually at stake.

## Modes

The skill runs in one of three modes. When the user just asks for help protecting their product, run **audit**.

| Mode | Command (plugin) | What it does | Writes |
|---|---|---|---|
| **scan** | `/fortify:scan` | Step 2 only — quick scanner pass, findings explained in plain words, top 3 fixes | Nothing |
| **audit** | `/fortify:audit` | Steps 1–5 — full assessment and tiered plan, then **stops** and offers to harden | `protection-assessment.md` |
| **harden** | `/fortify:harden` | Step 6 — implements the items the user picks from an existing report (runs audit first if none exists) | Code and build config, one reviewable change at a time |

## Workflow

### Step 1 — Understand the product (intake)

Find out, from the codebase first and questions second:

- **What it is and how it reaches users** — web app / SaaS, mobile app, desktop app, game, SDK or library, API, data product, AI/LLM product, firmware or hardware. Products are often several of these.
- **The crown jewels** — what would actually hurt to lose? Typical answers: a proprietary algorithm, a pricing or scoring engine, a curated dataset, a trained model or prompt chain, paid features, the UX itself, integrations, assets (art, 3D, audio).
- **Who they fear** — casual pirates, competitors cloning features, AI-assisted rebuilders, crackers removing licences, scrapers harvesting data, insiders.
- **Constraints** — budget, team skills, performance sensitivity, offline requirements, open-source obligations, target stores (Apple/Google rules).

If a repository is available, scan it before asking (Step 2) — many answers are already in the code. Ask at most 3–4 questions, only for what the code can't tell you. If the user isn't there to answer, assume the most likely answers, state them at the top of the report, and continue.

### Step 2 — Scan the codebase

Run the scanner that ships in this skill's `scripts/` folder (the folder this SKILL.md is in) against the project root. It needs only Python 3.8+ and the standard library, and is read-only:

```bash
python3 <this-skill-folder>/scripts/scan.py <project-root> --json <scratch-dir>/fortify-scan.json
```

Write the JSON somewhere temporary, not into the user's project.

It detects the stack and flags exposure issues: published source maps, secrets in client code, client-side premium checks, missing release minification, debuggable builds, missing rate limiting, Electron/Unity/Flutter/Rust/Python packaging weaknesses, open-source licence implications. Secrets are masked in its output; never print a full secret in the conversation or the report.

Treat scanner findings as leads, not verdicts: open the flagged files and confirm each one before it goes in the report. Then read the main entry points yourself to locate where the crown jewels live (client vs server).

No repository? Do the assessment from the user's description and say that the findings are based on description only.

### Step 3 — Assess the five clone vectors

Rate each vector **High / Medium / Low** risk = how exposed × how valuable × how easy. Use `references/platforms.md` for what attackers can extract on each platform.

| # | Vector | The question to answer |
|---|--------|------------------------|
| 1 | **Code extraction** | Can someone read or decompile the shipped code and lift the logic? (JS bundles, source maps, APKs, .NET/Java bytecode, Python, Electron asar, Unity Mono DLLs) |
| 2 | **Behavioural cloning** | Can someone rebuild it by using it, reading the docs and screenshots — with AI help? How much of the value is visible from the outside? |
| 3 | **Data & API harvesting** | Can someone scrape the data, call the API at scale, or distil the AI model through its outputs? |
| 4 | **Piracy & tampering** | Can someone unlock paid features, remove the licence check, or run a modified client? |
| 5 | **Secret & asset leakage** | Are API keys, prompts, model weights, private endpoints or paid assets shipped to the client or committed to the repo? |

Then assess the **moat** — what a clone could *not* copy: proprietary or network data, network effects, integrations and contracts, hardware, brand and trust, regulatory approvals, speed of iteration, support. A product with a strong moat needs less code hardening; a product whose only value is visible behaviour needs speed and brand more than obfuscation.

### Step 4 — Build the protection plan

Recommendations come in three tiers. Start every plan with the architectural question ("what can move to the server?").

- **Tier 1 — Quick wins** (hours, free): fix the scanner's confirmed findings, turn off source maps, enable release minification, move secrets server-side, add rate limits, register the trademark.
- **Tier 2 — Core protection** (days, low cost): move crown-jewel logic server-side, server-side entitlement checks, obfuscation suited to the platform, app attestation, licence validation, per-customer watermarking, data trap records, clone monitoring.
- **Tier 3 — Advanced** (weeks, often paid): code virtualization, commercial RASP, anti-tamper suites, hardware-bound licences, legal registrations (patents where they apply). Only when the stakes justify it.

For each recommendation give:
- **What** — in one plain sentence, term explained.
- **Why** — which vector and finding it addresses.
- **How** — the concrete tool or change for *their* stack (from `references/platforms.md`), with the config snippet when short.
- **Cost / effort / trade-off** — money, time, performance impact, debugging pain, store-policy risk.
- **How much it helps** — honestly: "stops casual copying", "adds days for a skilled attacker", "makes it impossible because the code is no longer shipped".

Include a **legal & business layer** from `references/legal.md` (copyright, trademark, ToS, trade secrets, database rights, patents, takedowns) and say clearly that it is general information, not legal advice. Include a **moat** section: what to invest in so that a clone, even a perfect one, doesn't win.

Where reliable recent facts matter (tool pricing, maintenance status, a new platform API), verify with a search instead of relying on the reference files, which can go stale.

### Step 5 — Deliver the report

Use the structure in `references/report-template.md`: executive summary with an overall exposure score, risk table per vector, confirmed findings, the tiered plan, legal and moat sections, and a short glossary of the terms used. Write it in the user's language. Save it as `protection-assessment.md` in the project root (or deliver it in the format the user prefers). Number every recommendation (T1-1, T1-2, T2-1 …) so the user can pick items for harden by number.

The report names real weaknesses and masked secret locations, so remind the user not to commit it to a public repository.

In **audit** mode, stop here: summarise the top three actions in chat and ask which items to harden.

### Step 6 — Implement (only with the user's go-ahead)

Offer to implement the Tier 1 items and any Tier 2 items the user picks (by number from the report). If there is no report yet, run the audit first. When implementing:
- Change build configs and code in small, reviewable steps; explain each change.
- Run the build and the tests after each change. Obfuscation and minification can break reflection, serialisation, dynamic imports and crash reporting — check those, and keep keep-rules/exclusions and symbol maps for crash symbolication stored privately.
- Never commit secrets; when moving a secret out of the client, tell the user to **rotate it**, since the old value must be assumed leaked.
- Do not add measures that harm users: no hidden destructive "punishment" code, no spyware-like telemetry, no hack-back. Telemetry used for licence or tamper detection must respect privacy law (GDPR in the EU) and be disclosed.
- Re-run the scanner at the end and show the before/after.

## Things to say no to (and what to offer instead)

- "Make it impossible to reverse engineer" → explain the limit, offer the strongest proportional plan.
- Code that damages a cracker's machine or data → illegal in most jurisdictions; offer detection, server-side lockout and legal routes.
- Obfuscating code whose licence (e.g. GPL) requires releasing source → flag the conflict; offer to separate proprietary parts.
- Help reverse engineering a competitor → out of scope for this skill.

## Reference files

- `references/platforms.md` — per-platform: what attackers extract, and the protection tools and settings (web, Node, Android, iOS, React Native, Flutter, Electron, .NET, Java, native C/C++/Rust, Python, Unity/Unreal, APIs/SaaS, data products, AI/LLM products).
- `references/glossary.md` — plain-language definitions of every term the report may use.
- `references/legal.md` — legal protection primer (EU/Portugal, US, general), with the limits of each.
- `references/report-template.md` — structure of the assessment report.
- `scripts/scan.py` — stack detection and exposure scanner.
