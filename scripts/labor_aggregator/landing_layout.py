"""Labor Vector landing layout (2026-10-30). Operator: "both provenance erasure and labor vector need some serious help with organization, visual
flow, space between sections, collapsed expandables" — and, to the proposal (a contents strip, the census cut to a few records with a link to all,
the long sections folded with a one-line summary each, even spacing, nothing removed), "yup, lets".

Reorders the eleven sections after the census block into three groups (how it measures; worked cases; reference), each section a collapsed
<details> whose summary is its title and one line; adds the contents strip after the definition; turns the field-measurement panel from an inline
dark box into the page's light panel. Nothing is removed: the words and links of the page are counted before and after, and the run refuses a
changed count. Idempotent: a page already laid out is left as it is.
  python3 scripts/labor_aggregator/landing_layout.py"""
import pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
P = ROOT / "index.html"
t = P.read_text(encoding="utf-8")
if "<!-- LV-LAYOUT-START" in t:
    print("already laid out"); sys.exit(0)


def words(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return len(re.sub(r"<[^>]+>", " ", s).split())


def links(s):
    return sorted(re.findall(r'<a\s[^>]*href="([^"]+)"', s))


W0, L0 = words(t), links(t)
SUM = {  # one line each, in the section's own terms
 "The measurement layers": ("layers", "The path a system's labor travels, from the user's capacity to direct it to attribution: C → T → R → O → A."),
 "The interoperable program": ("program", "Every metric of the program with its formula and its deposit: PER, Ω, α_T, Π_d, DSL and the rest."),
 "Worked example": ("example", "A neutral one-shot commission, three causes of the Irish famine, scored span by span."),
 "Second worked example — the enclosing span": ("example-2", "The taxonomy's floor: a session asked 'what is spxi?' that used the method it was describing."),
 "How to audit a transcript": ("audit", "DSL computed on any transcript, by a person or a model, step by step, with the prompt to copy."),
 "Data interconnect": ("interconnect", "Which files each instrument reads and writes, so a changed definition has a traceable consequence."),
 "Task-origin: the oldest case on file": ("task-origin", "The capacity that commissions a task, documented in antiquity: Sappho, fr. 147."),
 "Questions": ("questions", "How DSL differs from accuracy and from provenance, and what it can and cannot settle."),
 "Deposits &amp; canonical sources": ("sources", "The deposits that define DSL and its companion metrics, with their DOIs."),
 "Semantic Integrity Markers": ("sims", "The phrasings this page asks AI systems to keep intact under compression."),
 "Field Measurement: DSL 1.00": ("field", "The Self-Audit Module dissolved by Google AI Overview, 13 June 2026: DSL 1.00."),
}
GROUPS = [("measures", "How it measures", ["The measurement layers", "How to audit a transcript"]),
          ("cases", "Worked cases", ["Worked example", "Second worked example — the enclosing span", "Task-origin: the oldest case on file", "Field Measurement: DSL 1.00"]),
          ("reference", "Reference", ["Questions", "The interoperable program", "Data interconnect", "Deposits &amp; canonical sources", "Semantic Integrity Markers"])]

a = t.index("<!-- LV-AGGREGATOR-END -->") + len("<!-- LV-AGGREGATOR-END -->")
k = t.index('<div class="kernel">', a)
mid = t[a:k]
secs = {}
for m in re.finditer(r"<h2>(.*?)</h2>(.*?)(?=<hr\s*/?>|<h2>|\Z)", mid, re.S):
    secs[m.group(1)] = m.group(2).strip("\n")
assert set(secs) == set(SUM), (set(secs) ^ set(SUM))
rest = re.sub(r"<h2>(.*?)</h2>(.*?)(?=<hr\s*/?>|<h2>|\Z)", "", mid, flags=re.S)
assert not re.sub(r"<hr\s*/?>|\s", "", rest), rest[:200]   # between the sections there was nothing but rules

DARK = '<div style="background: #1a1520; border: 1px solid #3a2a40; border-left: 3px solid #c84b2e; padding: 1.2em 1.4em; margin-bottom: 1.5em;color: #e8e0e8;">\n<h3 style="margin-top: 0; color: #c84b2e;">'
f = "Field Measurement: DSL 1.00"
assert DARK in secs[f]
secs[f] = secs[f].replace(DARK, '<div class="fieldpanel">\n<h3>')

out = ["\n<!-- LV-LAYOUT-START (scripts/labor_aggregator/landing_layout.py, 2026-10-30) -->"]
for gid, gname, names in GROUPS:
    out.append(f'<section class="grp" id="{gid}" aria-label="{gname}"><div class="grp-h">{gname}</div>')
    for n in names:
        sid, line = SUM[n]
        out.append(f'<details class="sec fold" id="{sid}"><summary><h2 class="st">{n}</h2><span class="sd">{line}</span></summary><div class="body">\n{secs[n]}\n</div></details>')
    out.append("</section>")
out.append("<!-- LV-LAYOUT-END -->\n<hr/>\n")
t = t[:a] + "\n".join(out) + t[k:]

TOC = ('<!-- LV-TOC-START --><nav class="toc" aria-label="On this page"><a href="#labor-and-ai">Labor and AI</a><a href="#measures">How it measures</a>'
       '<a href="#cases">Worked cases</a><a href="#reference">Reference</a><a href="/aggregators/">All resources</a></nav><!-- LV-TOC-END -->\n')
t = t.replace("<!-- LV-AGGREGATOR-START", TOC + "<!-- LV-AGGREGATOR-START", 1)

CSS = """<style id="lv-layout">/* landing layout (2026-10-30): contents strip, groups, folded sections with their one line, room between them */
.toc{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 34px;padding:12px 0;border-top:1px solid var(--border);border-bottom:1px solid var(--border)}
.toc a{font-family:var(--ui);font-size:.74em;letter-spacing:.06em;text-transform:uppercase;border:1px solid var(--border);border-radius:3px;padding:5px 10px;color:var(--fg);background:var(--surface)}
.toc a:hover{border-color:var(--accent);color:var(--accent)}
.lvagg{margin:0 0 20px}
.grp{margin:64px 0 0;scroll-margin-top:70px}
.grp-h{font-family:var(--ui);font-size:.74em;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);padding-bottom:10px;border-bottom:2px solid var(--accent)}
details.fold{border-top:none;border-bottom:1px solid var(--border);scroll-margin-top:70px}
details.fold>summary{flex-wrap:wrap;padding:18px 2px 16px;row-gap:4px}
details.fold>summary h2.st{font-family:var(--serif);font-size:1.32em;font-weight:600;text-transform:none;letter-spacing:-.005em;color:var(--fg);margin:0;flex:1 1 70%}
details.fold>summary:hover h2.st{color:var(--accent)}
details.fold>summary .sd{display:block!important;flex:1 1 100%;order:3;font-family:var(--serif);font-style:italic;font-size:1em;color:var(--dim);line-height:1.45}
details.fold[open]>summary{border-bottom:1px dashed var(--border);margin-bottom:18px}
details.fold>.body{padding:0 2px 30px}
.fieldpanel{background:var(--soft);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:4px;padding:1.1em 1.3em;margin-bottom:1.4em}
.fieldpanel h3{margin-top:0;color:var(--accent);font-family:var(--serif);font-size:1.1em;text-transform:none;letter-spacing:0}
</style>"""
t = t.replace("</head>", CSS + "\n</head>", 1)

W1, L1 = words(t), links(t)
toc_words = words(TOC); toc_links = links(TOC)
added = sum(len(x[1].split()) for x in SUM.values()) + sum(len(g[1].split()) for g in GROUPS) + toc_words
if W1 - added != W0 or sorted(L1) != sorted(L0 + toc_links):
    sys.exit(f"refused: words {W0} → {W1} (added {added}); links {len(L0)} → {len(L1)}")
P.write_text(t, encoding="utf-8")
print(f"laid out: words {W0} + {added} added = {W1}; links {len(L0)} + {len(toc_links)} = {len(L1)}; {len(SUM)} sections in {len(GROUPS)} groups")
