# Fortify (plugin)

Assess how easily a software product can be reverse engineered, cracked, scraped or cloned, then get a tailored protection plan in plain language, and apply it. Defensive only, honest about limits.

Bundles the **skill** (`skills/fortify/`) and three **commands** (`commands/`), namespaced once installed:

| Command | What it does |
|---|---|
| `/fortify:scan [path]` | Quick read-only scan with findings in plain words |
| `/fortify:audit [path] [notes]` | Full assessment → `protection-assessment.md` with a numbered, tiered plan |
| `/fortify:harden [items]` | Applies chosen items one reviewable change at a time, then re-scans |

Full documentation is in the skill's own README: [`skills/fortify/README.md`](skills/fortify/README.md). See the [repository root README](../../README.md) for installation.
