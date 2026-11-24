#!/usr/bin/env python3
"""Draw architecture.svg, the picture at the top of the README.

The estate is read left to right, from source to the people it serves, with
one arrow colour per kind of interaction. It is drawn here and not in Mermaid
because Mermaid chooses its own layout and cannot be told that source is on
the left.

Standard library only. Edit the boxes and arrows below, then:

    python3 docs/architecture.py

and commit the script and the SVG together.
"""
from pathlib import Path

W, H = 1680, 1040
INK, MUTED, LINE, PAPER = "#0f172a", "#475569", "#cbd5e1", "#ffffff"
DEPLOY, SERVE, OBSERVE, ALERT = "#2563eb", "#16a34a", "#d97706", "#dc2626"
FONT = "Inter, system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
out: list[str] = []
add = out.append


def text(x, y, s, size=14, weight=400, fill=INK, anchor="start"):
    add(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}">{s}</text>')


def glyph(kind, x, y, colour):
    """A 34px badge with a white pictogram built from primitives."""
    add(f'<rect x="{x}" y="{y}" width="34" height="34" rx="8" fill="{colour}"/>')
    g = lambda body: add(f'<g transform="translate({x},{y})" fill="none" stroke="#fff" '
                         f'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{body}</g>')
    if kind == "repo":  # a branch
        g('<path d="M11 9v16M11 17c8 0 12-2 12-8"/><circle cx="11" cy="9" r="2.4" fill="#fff"/>'
          '<circle cx="11" cy="25" r="2.4" fill="#fff"/><circle cx="23" cy="9" r="2.4" fill="#fff"/>')
    elif kind == "check":
        g('<path d="M9 18l5 5 11-12"/>')
    elif kind == "box":
        g('<path d="M8 13l9-5 9 5v9l-9 5-9-5zM8 13l9 5 9-5M17 18v9"/>')
    elif kind == "sync":
        g('<path d="M25 14a9 9 0 0 0-16-2M9 20a9 9 0 0 0 16 2"/><path d="M9 7v6h6M25 27v-6h-6"/>')
    elif kind == "grid":
        g('<rect x="8" y="8" width="7" height="7"/><rect x="19" y="8" width="7" height="7"/>'
          '<rect x="8" y="19" width="7" height="7"/><rect x="19" y="19" width="7" height="7"/>')
    elif kind == "phone":
        g('<rect x="11" y="6" width="12" height="22" rx="2.5"/><path d="M15.5 24h3"/>')
    elif kind == "house":
        g('<path d="M7 17l10-9 10 9M10 15v11h14V15"/>')
    elif kind == "chart":
        g('<path d="M9 26V17M17 26V9M25 26V13"/>')
    elif kind == "chip":
        g('<rect x="10" y="10" width="14" height="14" rx="2"/><path d="M14 6v4M20 6v4M14 24v4M20 24v4M6 14h4M6 20h4M24 14h4M24 20h4"/>')
    elif kind == "disks":
        g('<ellipse cx="17" cy="10" rx="9" ry="3.5"/><path d="M8 10v14c0 2 4 3.5 9 3.5s9-1.5 9-3.5V10M8 17c0 2 4 3.5 9 3.5s9-1.5 9-3.5"/>')
    elif kind == "lock":
        g('<rect x="9" y="15" width="16" height="12" rx="2"/><path d="M12 15v-3a5 5 0 0 1 10 0v3"/>')
    elif kind == "tv":
        g('<rect x="6" y="9" width="22" height="14" rx="2"/><path d="M13 27h8"/>')


def card(x, y, w, h, title, sub, kind, colour, sub2=None):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{PAPER}" stroke="{LINE}" stroke-width="1.5"/>')
    glyph(kind, x + 14, y + 14, colour)
    text(x + 58, y + 30, title, 15, 700)
    text(x + 58, y + 49, sub, 12.5, 400, MUTED)
    if sub2:
        text(x + 58, y + 66, sub2, 12.5, 400, MUTED)


def group(x, y, w, h, title, tint, edge, rows):
    """A titled panel of chips. `rows` is a list of rows; a chip is 'Name|role'."""
    if isinstance(rows[0], str):
        rows = [rows]
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{tint}" stroke="{edge}" stroke-width="1.5"/>')
    text(x + 14, y + 22, title, 12.5, 700, edge)
    gap = 8
    ch = (h - 44 - gap * (len(rows) - 1)) / len(rows)
    for r, chips in enumerate(rows):
        cy = y + 32 + r * (ch + gap)
        cw = (w - 28 - gap * (len(chips) - 1)) / len(chips)
        for i, c in enumerate(chips):
            cx = x + 14 + i * (cw + gap)
            add(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cw:.1f}" height="{ch:.1f}" rx="8" fill="{PAPER}" stroke="{edge}" stroke-opacity=".45"/>')
            lines = c.split("|")
            base = cy + ch / 2 + 4.5 - (len(lines) - 1) * 7.5
            for j, ln in enumerate(lines):
                text(cx + cw / 2, base + j * 15, ln, 12.5, 600 if j == 0 else 400, INK if j == 0 else MUTED, "middle")


def stat(x, y, big, small):
    text(x, y, big, 26, 800)
    text(x, y + 20, small, 12.5, 400, MUTED)


def tile(x, y, w, title, kind, colour, stats):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="118" rx="12" fill="{PAPER}" stroke="{LINE}" stroke-width="1.5"/>')
    glyph(kind, x + 14, y + 14, colour)
    text(x + 58, y + 36, title, 12.5, 700, colour)
    step = (w - 30) / max(len(stats), 1)
    for i, (big, small) in enumerate(stats):
        stat(x + 22 + i * step, y + 82, big, small)


def flow(x1, y1, x2, y2, colour, label=None, bend=0.5, lx=None, ly=None):
    mx = x1 + (x2 - x1) * bend
    add(f'<path d="M{x1} {y1} C{mx} {y1} {mx} {y2} {x2 - 9} {y2}" fill="none" stroke="{colour}" '
        f'stroke-width="3.2" marker-end="url(#a{colour[1:]})"/>')
    if label:
        text(lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else min(y1, y2) - 9, label, 12, 600, colour, "middle")


def rise(x, y1, y2, colour, label=None):
    add(f'<path d="M{x} {y1} L{x} {y2 + 9}" fill="none" stroke="{colour}" stroke-width="3.2" marker-end="url(#a{colour[1:]})"/>')
    if label:
        text(x + 12, (y1 + y2) / 2 + 5, label, 12, 600, colour)


# ------------------------------------------------------------------ canvas
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">')
add("<defs>" + "".join(
    f'<marker id="a{c[1:]}" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="4.2" markerHeight="4.2" orient="auto">'
    f'<path d="M0 0l10 5-10 5z" fill="{c}"/></marker>' for c in (DEPLOY, SERVE, OBSERVE, ALERT)) + "</defs>")
add(f'<rect width="{W}" height="{H}" rx="18" fill="#f8fafc" stroke="{LINE}"/>')

# ---- the four stages, as one chevron strip: the reading direction is the picture
stages = [("1", "Source", 40, 300), ("2", "Delivery", 350, 670), ("3", "Production", 750, 1310), ("4", "People", 1380, 1640)]
for n, name, x0, x1 in stages:
    add(f'<path d="M{x0} 36h{x1 - x0 - 22}l22 24-22 24h-{x1 - x0 - 22}l22-24z" fill="{INK}"/>')
    add(f'<circle cx="{x0 + 46}" cy="60" r="13" fill="#fff"/>')
    text(x0 + 46, 65.5, n, 15, 800, INK, "middle")
    text(x0 + 70, 66, name, 17, 700, "#fff")

# ---- 1 source
card(40, 150, 260, 90, "homelab-pim-tools", "service code", "repo", INK)
card(40, 300, 260, 400, "homelab-gitops", "desired state of the estate", "repo", INK)
for yy, a, b in ((372, "charts + apps", "what runs in the cluster"), (627, "tofu/", "every VM and container")):
    add(f'<rect x="56" y="{yy - 4}" width="228" height="58" rx="8" fill="#f1f5f9"/>')
    text(70, yy + 20, a, 13.5, 700)
    text(70, yy + 39, b, 12.5, 400, MUTED)

# ---- 2 delivery
card(350, 150, 320, 90, "Build pipeline", "tests, scans and builds the image,", "check", DEPLOY, "then publishes it for the cluster")
card(350, 355, 320, 90, "ArgoCD", "pulls git, syncs the cluster to it", "sync", DEPLOY)
card(350, 610, 320, 90, "OpenTofu", "plans and applies every guest", "grid", DEPLOY)

# ---- 3 production
PX = 750
add(f'<rect x="{PX}" y="112" width="560" height="644" rx="16" fill="#eef2ff" stroke="#6366f1" stroke-width="1.5" stroke-dasharray="6 5"/>')
text(PX + 18, 134, "PROXMOX HYPERVISOR", 11.5, 700, "#4338ca")
add(f'<rect x="{PX + 18}" y="146" width="524" height="380" rx="14" fill="{PAPER}" stroke="{LINE}" stroke-width="1.5"/>')
text(PX + 34, 168, "JBK8S01 · k3s cluster", 13.5, 700)
group(PX + 34, 180, 492, 96, "CHAT + PERSONAL DATA", "#f0fdf4", "#15803d", ["Open WebUI|chat", "pim-tools|tool server", "Radicale|calendar · tasks", "Syncthing|notes vault"])
group(PX + 34, 290, 492, 96, "PHOTOS + MEDIA", "#faf5ff", "#7e22ce", ["Immich|photo library", "Postgres|Immich's database", "Tautulli|Plex watch history"])
group(PX + 34, 400, 492, 110, "OBSERVABILITY", "#fffbeb", "#b45309", ["Prometheus|metrics · alerts", "Loki|logs", "Tempo|traces", "Grafana|dashboards"])
group(PX + 18, 574, 524, 162, "VIRTUAL MACHINES + CONTAINERS", "#eff6ff", "#1d4ed8", [
    ["JBDNS01|DNS · DHCP", "JBNAS01|NAS storage", "JBVM01|jump box", "JBVM02|ops · chat brain"],
    ["JBVM03|application server", "JBVM04|application server", "JBLLM01|LLM server"],
])
card(PX + 18, 790, 250, 70, "NVIDIA Shield", "Plex Media Server", "tv", MUTED)

# ---- 4 people
card(1380, 183, 260, 90, "Phone", "chat · calendar · tasks", "phone", SERVE, "photos")
card(1380, 410, 260, 90, "Operator", "dashboards · Discord alerts", "chart", OBSERVE)
card(1380, 610, 260, 90, "Household", "DNS · storage · media · apps", "house", SERVE)

# ---- deploy: source to production, left to right
flow(300, 195, 350, 195, DEPLOY)
flow(670, 195, PX + 34, 228, DEPLOY)
flow(300, 400, 350, 400, DEPLOY)
flow(670, 400, PX + 18, 338, DEPLOY)
flow(300, 655, 350, 655, DEPLOY)
flow(670, 655, PX + 18, 655, DEPLOY)
# ---- serve: production to people
flow(PX + 526, 228, 1380, 228, SERVE)
flow(PX + 526, 338, 1380, 250, SERVE)
flow(PX + 542, 655, 1380, 655, SERVE)
flow(PX + 268, 825, 1380, 680, SERVE, bend=0.75)
# ---- observe: every guest reports up into observability, which reports to the operator
rise(PX + 280, 574, 510, OBSERVE)
flow(PX + 526, 440, 1380, 440, OBSERVE)
flow(PX + 526, 472, 1380, 472, ALERT)

# ---- legend: the arrows themselves, one word each
lx, ly = 40, 790
add(f'<rect x="{lx}" y="{ly}" width="630" height="70" rx="12" fill="{PAPER}" stroke="{LINE}"/>')
for i, (c, word) in enumerate(((DEPLOY, "deploy"), (SERVE, "serve"), (OBSERVE, "observe"), (ALERT, "alert"))):
    x = lx + 26 + i * 156
    add(f'<path d="M{x} {ly + 35} h46" stroke="{c}" stroke-width="3.2" marker-end="url(#a{c[1:]})"/>')
    text(x + 66, ly + 40, word, 14.5, 700, c)
# ---- the facts underneath: what it runs on, and how it is reached
tile(40, 892, 520, "HARDWARE: ONE RYZEN 7 2700X HOST", "chip", INK, [("16", "CPU threads"), ("128 GB", "DDR4 memory"), ("8", "guests · 38 vCPU")])
tile(580, 892, 520, "STORAGE: ZFS ON THE NAS", "disks", "#1d4ed8", [("2", "RAIDZ1 pools"), ("8 TB", "media on 4 HDD"), ("1.4 TB", "data on 4 SSD")])
tile(1120, 892, 520, "REMOTE ACCESS: TAILSCALE VPN", "lock", SERVE, [])
for n, line in enumerate((
    "Nothing is open to the internet. Phones and laptops join a private",
    "WireGuard network and reach every host through one router on the LAN.",
    "Away from home they can route all their traffic through it too.",
)):
    text(1142, 954 + n * 19, line, 13, 400, INK)
add("</svg>")
Path(__file__).with_name("architecture.svg").write_text("\n".join(out) + "\n")
