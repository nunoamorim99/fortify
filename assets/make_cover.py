"""Render the Fortify README cover (dark glassy suite style) to SVG + PNG.

Usage: python3 assets/make_cover.py assets/cover.svg assets/cover.png
Needs: pip install cairosvg; Fira Sans and Spectral fonts installed system-wide.
"""
import sys
import cairosvg

W, H = 1600, 600
CX, CY = 1170, 300
TEAL, CYAN, VIOLET = "#2dd4bf", "#22d3ee", "#8b5cf6"


def shield(scale):
    # Unit shield: flat-ish crown, straight shoulders, pointed base.
    pts = dict(tl=(-0.82, -0.86), top=(0, -1.0), tr=(0.82, -0.86),
               sr=(0.82, 0.02), bot=(0, 1.04), sl=(-0.82, 0.02))
    def p(name, dx=0.0, dy=0.0):
        x, y = pts[name]
        return f"{CX + (x + dx) * scale:.1f},{CY + (y + dy) * scale:.1f}"
    return (f"M {p('tl')} Q {p('top', 0, -0.02)} {p('tr')} L {p('sr')} "
            f"Q {p('sr', 0, 0.66)} {p('bot')} Q {p('sl', 0, 0.66)} {p('sl')} Z")


grid = "".join(
    f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="#ffffff" stroke-opacity="0.025"/>' for x in range(0, W, 80)
) + "".join(
    f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#ffffff" stroke-opacity="0.025"/>' for y in range(0, H, 80)
)

layers = [  # outer → inner: defence in depth
    (262, "LEGAL &amp; MOAT", 0.30),
    (204, "RUNTIME", 0.45),
    (148, "HARDENING", 0.65),
    (94, "ARCHITECTURE", 0.95),
]
shields, labels = [], []
for i, (s, label, op) in enumerate(layers):
    shields.append(
        f'<path d="{shield(s)}" fill="url(#glass)" fill-opacity="{0.55 + i * 0.12:.2f}" '
        f'stroke="url(#edge)" stroke-opacity="{op}" stroke-width="{1.4 + i * 0.5:.1f}"/>'
    )
    # leader from this layer's straight right edge to a label column clear of all layers
    lx = CX + 0.82 * s
    ly = 110 + i * 60
    col = CX + 0.82 * layers[0][0] + 26
    labels.append(
        f'<line x1="{lx:.0f}" y1="{ly}" x2="{col:.0f}" y2="{ly}" stroke="{TEAL}" stroke-opacity="{op * 0.7:.2f}" stroke-dasharray="2 4"/>'
        f'<circle cx="{lx:.0f}" cy="{ly}" r="2.5" fill="{TEAL}" fill-opacity="{op}"/>'
        f'<text x="{col + 10:.0f}" y="{ly + 4}" font-family="Fira Sans" font-weight="500" font-size="13" '
        f'letter-spacing="2.5" fill="#cbd5e1" fill-opacity="{0.45 + op * 0.5:.2f}">{label}</text>'
    )

# incoming "probes" that stop at the outer layer
probes = ""
for (x1, y1, x2, y2) in [(1560, 560, 1395, 360), (1300, 590, 1250, 495), (860, 520, 985, 455), (880, 70, 1000, 125)]:
    probes += (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{VIOLET}" stroke-opacity="0.55" '
               f'stroke-width="1.5" stroke-dasharray="3 7"/>'
               f'<circle cx="{x2}" cy="{y2}" r="3.5" fill="{VIOLET}" fill-opacity="0.9"/>'
               f'<circle cx="{x2}" cy="{y2}" r="9" fill="none" stroke="{VIOLET}" stroke-opacity="0.35"/>')

svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="glow" cx="{CX / W:.3f}" cy="0.5" r="0.45">
      <stop offset="0" stop-color="{TEAL}" stop-opacity="0.22"/>
      <stop offset="0.5" stop-color="{CYAN}" stop-opacity="0.06"/>
      <stop offset="1" stop-color="#0d1117" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glow2" cx="0.08" cy="0.1" r="0.5">
      <stop offset="0" stop-color="{VIOLET}" stop-opacity="0.12"/>
      <stop offset="1" stop-color="#0d1117" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.07"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0.015"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{CYAN}"/>
      <stop offset="0.6" stop-color="{TEAL}"/>
      <stop offset="1" stop-color="{VIOLET}"/>
    </linearGradient>
    <linearGradient id="title" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#f8fafc"/>
      <stop offset="1" stop-color="#99f6e4"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="#0d1117"/>
  {grid}
  <rect width="{W}" height="{H}" fill="url(#glow)"/>
  <rect width="{W}" height="{H}" fill="url(#glow2)"/>
  {probes}
  {''.join(shields)}
  {''.join(labels)}
  <text x="{CX}" y="{CY + 16}" text-anchor="middle" font-family="Fira Sans" font-weight="600" font-size="46"
        fill="#e2fdf8">{{ }}</text>
  <circle cx="{CX}" cy="{CY + 52}" r="3" fill="{TEAL}"/>

  <text x="110" y="200" font-family="Fira Sans" font-weight="500" font-size="15" letter-spacing="5"
        fill="{TEAL}">A CLAUDE CODE SKILL</text>
  <text x="104" y="320" font-family="Fira Sans" font-weight="700" font-size="128" letter-spacing="10"
        fill="url(#title)">FORTIFY</text>
  <line x1="110" y1="356" x2="230" y2="356" stroke="url(#edge)" stroke-width="3"/>
  <text x="110" y="408" font-family="Spectral" font-size="31" fill="#e2e8f0">Know what can be copied.</text>
  <text x="110" y="448" font-family="Spectral" font-style="italic" font-size="31" fill="#94a3b8">Protect what matters.</text>
  <text x="110" y="520" font-family="Fira Sans" font-weight="500" font-size="16" letter-spacing="2"
        fill="#64748b">/fortify:scan   ·   /fortify:audit   ·   /fortify:harden</text>
</svg>'''

out_svg, out_png = sys.argv[1], sys.argv[2]
open(out_svg, "w").write(svg)
cairosvg.svg2png(bytestring=svg.encode(), write_to=out_png, output_width=W, output_height=H)
print("ok")
