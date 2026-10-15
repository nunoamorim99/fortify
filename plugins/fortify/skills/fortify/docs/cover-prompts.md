# Fortify — cover art prompts (Higgsfield)

Ready-to-run prompts for generating marketing cover art in a Higgsfield-connected environment
(e.g. Claude Code with the Higgsfield MCP). Model: **`nano_banana_pro`** — it renders in-image text
("FORTIFY") most reliably. Aspect ratio: **wide banner (16:9 or ~3:1)** for a README header,
**1:1** for LinkedIn. Keep the shared **style prefix** on every prompt for a consistent set.

The bundled designed cover (`docs/assets/cover.png`) is precise SVG art; use these prompts for
richer social/marketing variants.

---

## Shared style prefix (prepend to every prompt)

> Cinematic cover art for a developer security tool, dark slate background (#0d1117), glassy
> translucent layered panels, soft ambient teal and cyan glow with a hint of violet, clean modern
> sans-serif display typography, generous negative space, premium and calm — no clutter, no
> skulls, no hooded hackers, no padlock clichés, no photographic realism.

## Variant 1 — Defence in depth

> …four nested glass shields, each slightly larger and fainter, around a small glowing pair of
> code braces "{ }"; thin dotted probe lines approach from the edges and stop at the outermost
> layer; the word **"FORTIFY"** large on the left, with a smaller line "Know what can be copied.
> Protect what matters."

## Variant 2 — The blueprint and the bastion

> …a translucent architectural blueprint of an app interface on the left gradually turning into the
> stone-and-glass walls of a modern bastion on the right, glowing seams of light where the code
> becomes walls; the title **"FORTIFY"** set in wide-tracked capitals across the upper third.

## Variant 3 — Clone and original

> …two identical glass app silhouettes side by side; the left one is hollow and wireframe, the right
> one is solid, lit from within by a warm core labelled with tiny icons of data, people and
> connections (the moat); the title **"FORTIFY"** centred above, small text "a Claude Code skill".

---

## Tips

- Generate 2–4 per variant and pick; regenerate if "FORTIFY" is misspelled rather than editing it.
- Keep the style prefix identical across a batch so the set looks like a family.
- For precise labels or diagrams, edit `assets/make_cover.py` and re-render instead.
