"""Render the Labor Vector meta-aggregator (labor census schema 1.0): an index and one page per resource, from
data/labor-census/census.json, and the worked research questions from data/labor-census/questions.json. Each record page
carries two JSON-LD nodes: the record (ours) and the entity it describes (theirs). Every quoted field shows its source, the
date read and the hash of the saved copy. Also writes /assets/lv.css (the shared design system), the landing page's top bar
and aggregator block between their markers, sitemap and llms.txt entries.
Run from the repository root: python3 scripts/labor_aggregator/build.py"""
import json, html, pathlib, re
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[1]
D = json.load(open(ROOT / "data/labor-census/census.json", encoding="utf-8")); ROWS = D["rows"]; BY = {r["slug"]: r for r in ROWS}
QS = json.load(open(ROOT / "data/labor-census/questions.json", encoding="utf-8"))["questions"]
SITE = "https://www.laborvector.org"; BASE = SITE + "/aggregators/"
OUT = ROOT / "aggregators"
e = lambda s: html.escape(str(s), quote=True)
CSS = open(HERE / "style.css", encoding="utf-8").read()
BASIS = {"operator": ("op", "the resource's own statement"), "third_party": ("3p", "a third-party account"), "third-party": ("3p", "a third-party account"),
         "observed": ("obs", "our observation"), "reading": ("rd", "our reading")}
INTER = D["intersections"]
SHORT = {"labor-producing-ai": "Labor producing AI", "ai-governing-labor": "AI governing labor", "labor-with-ai": "Labor performed with AI",
         "gains-and-losses": "Gains and losses", "worker-power": "Worker power"}
KINDS = D["evidence_kinds"]
REL = {"part_of": "Part of", "has_part": "Has part", "neighbour": "Neighbours", "uses": "Uses", "used_by": "Used by", "sibling": "Sibling record",
       "capture": "Captures: the composition layer's account", "non_row": "The /non row"}
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">')
HEAD = FONTS + '<link rel="stylesheet" href="/assets/lv.css">'
NAV = [("DSL", "/#dsl"), ("Labor and AI", "/aggregators/"), ("Questions", "/aggregators/#questions"), ("Captures", "https://www.alexanarch.org/captures/")]


def topbar(on=""):
    nav = "".join(f'<a class="{"on" if n == on else ""}" href="{u}">{n}</a>' for n, u in NAV)
    return (f'<header class="top"><div class="in"><a class="wm" href="/"><i></i>Labor Vector</a><nav class="nav-top">{nav}</nav><div class="sp"></div>'
            f'<form class="srch" action="/aggregators/" method="get" role="search"><input name="q" type="search" placeholder="Search {len(ROWS)} resources" aria-label="Search the resources"></form></div></header>')


def signup(follow=None, name=None):
    """An email box. Posts to /api/subscribe, which stores the address privately (see /privacy)."""
    if follow:
        h, t = f"Follow {e(name)}", "An email when this record changes: the resource ends, comes back, changes hands, or publishes new findings."
    else:
        h, t = "The Labor Vector digest", "New records in the labor and AI census, changes to the resources it follows, and new worked questions, by email, now and then."
    return (f'<form class="signup" action="/api/subscribe" method="post">'
            f'<h4>{h}</h4><p>{t}</p><div class="fr"><input type="email" name="email" required placeholder="you@example.org" autocomplete="email" aria-label="Email address">'
            f'<button class="btn" type="submit">{"Follow" if follow else "Subscribe"}</button></div>'
            + (f'<input type="hidden" name="follow" value="{e(follow)}">' if follow else "")
            + '<input type="hidden" name="page" value=""><span class="trap" aria-hidden="true"><input type="text" name="website" tabindex="-1" autocomplete="off"></span>'
            '<label class="ok"><input type="checkbox" name="consent" value="yes" required><span>Email me from Labor Vector about this. My address is stored privately and never published; '
            'every email carries a one-click unsubscribe. <a href="/privacy">Privacy</a></span></label><p class="msg" role="status"></p></form>')
SIGNUP_JS = ("<script>document.querySelectorAll('form.signup').forEach(f=>{f.page.value=location.pathname;f.onsubmit=async ev=>{ev.preventDefault();const m=f.querySelector('.msg'),b=f.querySelector('button');"
             "b.disabled=true;m.className='msg';m.textContent='Saving…';try{const r=await fetch(f.action,{method:'POST',headers:{'Accept':'application/json','Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(new FormData(f))});"
             "const j=await r.json().catch(()=>({}));if(r.ok){m.className='msg good';m.textContent='You are on the list. Thank you.';f.email.value=''}else{m.className='msg bad';m.textContent=j.error||'That did not work. Please try again.'}}"
             "catch(_){m.className='msg bad';m.textContent='That did not work. Please try again.'}b.disabled=false}})</script>")
PRIVACY = ("<p>Labor Vector asks for one thing: an email address, typed in by the person who owns it, with a box ticked to agree to the emails.</p>"
           "<h2>What is stored</h2><p>The address, which list it joined (the digest, or a follow of one record, and which), the date, and the page the form was on. Nothing else: no name, no IP address, no tracking.</p>"
           "<h2>Where</h2><p>In a private store of the site's host, Vercel, shared with its sibling sites machinemediation.org and provenanceerasure.org. Private means no web address serves the records; only the sites' own signup code and their operator can read them. Addresses are never published, sold or shared.</p>"
           "<h2>What it is used for</h2><p>The emails the person asked for: the digest, or notice that a followed record changed. No email has been sent yet; the list is gathered first. Every email will carry a one-click unsubscribe, and an unsubscribe removes the address from that list.</p>"
           "<h2>Removal</h2><p>Anyone can ask for their address to be deleted entirely, from any email, and it is.</p>")
def simple_page(path, title, body):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} — Labor Vector</title>'
            f'<link rel="canonical" href="{SITE}{path}"><meta name="robots" content="noindex">{HEAD}</head><body>{topbar()}<div class="wrap"><div class="crumb"><a href="/">Labor Vector</a> / {e(title.lower())}</div>'
            f'<h1>{e(title)}</h1><div class="kernel">{body}</div><div class="foot">Labor Vector · laborvector.org · editor Lee Sharks</div></div></body></html>')

def bchip(r, f):
    v = r["evidence"].get(f)
    if not v: return ""
    ab, full = BASIS.get(v.get("basis"), ("rd", "our reading"))
    tip = full + (f' · “{v["quote"]}”' if v.get("quote") else "")
    return f' <a class="bl" href="#ev-{e(f)}" title="{e(tip)}"><span class="b">{ab}</span></a>'


def fold(title, inner, n=None, desc="", open_=False):
    if not inner: return ""
    return (f'<details class="sec"{" open" if open_ else ""}><summary><span class="st">{title}</span><span class="sd">{desc}</span>'
            + (f'<span class="sn">{n}</span>' if n else "") + f'</summary><div class="body">{inner}</div></details>')


def kinds(r):
    return '<span class="cap">' + "".join(f'<span class="on">{e(k)}</span>' for k in r["evidence_kind"]) + "</span>"


CHIP_KIND = {"global, radically participatory research initiative": "participatory research initiative"}


def short_kind(k):
    """The kind's head, for a chip: the phrase before its first colon, parenthesis or comma; the full kind stays in the kernel and the entity table."""
    import re as _re
    if k in CHIP_KIND: return CHIP_KIND[k]
    for full, lab in CHIP_KIND.items():
        if k.startswith(full): return lab
    h = _re.split(r":| \(|, | with | published | built ", k, maxsplit=1)[0].strip()
    h = h.replace("working paper and monthly-updated dashboard", "working paper and dashboard")
    return h if len(h) <= 42 else h[:40].rsplit(" ", 1)[0] + "…"


def chips(r):
    st = r["lifecycle"]["state"]; c = {"ended": "dead", "active": "live"}.get(st, "")
    return ('<div class="chips">' + "".join(f'<span class="chip">{e(SHORT.get(i, i))}</span>' for i in r["intersections"][:2])
            + f'<span class="chip" title="{e(r["kind"])}">{e(short_kind(r["kind"]))}</span><span class="chip {c}">{e(st)}</span></div>')


def kernel(r):
    k = r["kind"]; art = "an" if k[:1].lower() in "aeiou" else "a"
    return f'{r["name"]}: {art} {k}. Operator: {r["operator"]}. Its unit: {r["unit"]}. Whose labor: {r["labor_object"]}.'


def cite_text(r):
    return f'Lee Sharks, ed. "{r["name"]}." Labor Vector meta-aggregator, laborvector.org, compiled {D["compiled"]}. {BASE}{r["slug"]}'


def bibtex(r):
    key = "lv-" + r["slug"].replace("-", "")[:24] + D["compiled"][:4]
    return (f'@misc{{{key},\n  editor = {{Sharks, Lee}},\n  title = {{{r["name"]}}},\n  howpublished = {{Labor Vector meta-aggregator, laborvector.org}},\n'
            f'  year = {{{D["compiled"][:4]}}},\n  note = {{Compiled {D["compiled"]}; every field sourced and dated}},\n  url = {{{BASE}{r["slug"]}}}\n}}')


def jsonld(r):
    rec, ent = BASE + r["slug"], BASE + r["slug"] + "#entity"
    k = r["kind"].lower()
    sch = "Dataset" if any(w in k for w in ("database", "dataset", "index", "tracker", "inventory", "benchmark", "monitor")) else \
          "Organization" if any(w in k for w in ("organisation", "organization", "collective", "union", "charity")) else "CreativeWork"
    entity = {"@id": ent, "@type": sch, "name": r["name"], "alternateName": r.get("aka", []), "url": r["url"]}
    if sch != "Organization": entity["creator"] = {"@type": "Organization", "name": r["operator"]}
    sd = r["evidence"].get("self_description") or {}
    if sd.get("quote"): entity["description"] = sd["quote"]
    for x in r.get("relations", []):
        if x["rel"] == "part_of" and x.get("target"): entity["isPartOf"] = {"@id": BASE + x["target"] + "#entity"}
    record = {"@id": rec, "@type": "WebPage", "name": f'{r["name"]} — Labor Vector meta-aggregator record', "mainEntity": {"@id": ent}, "about": {"@id": ent},
              "abstract": kernel(r), "dateCreated": D["compiled"], "dateModified": D["compiled"],
              "publisher": {"@type": "Organization", "name": "Labor Vector", "url": SITE + "/"},
              "editor": {"@type": "Person", "name": "Lee Sharks", "identifier": "https://orcid.org/0009-0000-1599-0703"},
              "isPartOf": {"@type": "Dataset", "name": "Labor Vector meta-aggregator", "url": BASE},
              "citation": [s["url"] for s in r["sources"].values()], "license": "https://creativecommons.org/licenses/by/4.0/"}
    return json.dumps({"@context": "https://schema.org", "@graph": [record, entity]}, ensure_ascii=False, indent=1).replace("</", "<\\/")


def link(slug):
    x = BY.get(slug); return f'<a href="/aggregators/{slug}">{e(x["name"])}</a>' if x else e(slug)


def lst(v):
    return e("; ".join(v)) if isinstance(v, list) else e(v or "")


def page(r):
    vt = "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in (r.get("version_and_time") or {}).items())
    cnt = f'{e(r["count"]["value"])} <span class="d">(as of {e(r["count"]["as_of"])})</span>' if r.get("count") else ""
    cov = r.get("coverage") or {}
    dr = r.get("direction") or {}
    DIR = (f'<div class="dir"><div><span>Supplies the labor</span><b>{e(dr.get("supplies", "not recorded"))}</b></div>'
           f'<div><span>Directs it</span><b>{e(dr.get("directs", "not recorded"))}</b></div>'
           f'<div><span>Receives the gains, bears the costs</span><b>{e(dr.get("gains", "not recorded"))}</b></div></div>')
    REC = [("intersections", "Intersections", e("; ".join(INTER.get(i, i) for i in r["intersections"]))),
           ("evidence_kind", "Kind of evidence", kinds(r)), ("unit", "Unit of record", e(r["unit"])),
           ("labor_object", "Whose labor", e(r["labor_object"])), ("method", "Method", e(r["method"])),
           ("coverage", "Coverage", e("; ".join(f"{k}: {v}" for k, v in cov.items()))),
           ("findings", "What it finds", lst(r["findings"])), ("stated_limits", "Its stated limits", lst(r["stated_limits"]))]
    ENT = [("name", "Canonical name", e(r["name"])), ("aka", "Also known as", e(", ".join(r.get("aka", [])))),
           ("url", "Address", f'<a href="{e(r["url"])}">{e(r["url"])}</a>'), ("operator", "Operator", e(r["operator"])),
           ("founded", "Founded", e(r.get("founded") or "")), ("kind", "Kind", e(r["kind"])),
           ("lifecycle", "Lifecycle", e(r["lifecycle"]["state"] + (f' — {r["lifecycle"]["detail"]}' if r["lifecycle"].get("detail") else ""))),
           ("count", "Count", cnt), ("cadence", "Cadence", e(r.get("cadence") or "")),
           ("data_access", "Data access", e(r.get("data_access") or "")), ("license", "Licence", e(r.get("license") or "")),
           ("version_and_time", "Versions and dates", e(vt)), ("observed", "Observation", e(f'{r["observed"]["on"]}: {r["observed"]["fetch"]}'))]
    tbl = lambda F: "".join(f'<tr><td>{k}</td><td>{v}{bchip(r, f)}</td></tr>' for f, k, v in F if v)
    own = r["evidence"].get("self_description")
    ownq = (f'<blockquote class="q">{e(own["quote"])}</blockquote><p class="d">{"In its own words" if own.get("basis") == "operator" else "As a third party describes it"}: '
            f'<a href="{e(r["sources"][own["src"]]["url"])}">{e(r["sources"][own["src"]]["url"])}</a>, read {e(r["sources"][own["src"]]["read"])}</p>') if own and own.get("quote") else ""
    ans = "".join(f"<li>{e(x)}</li>" for x in r.get("answers") or [])
    nans = "".join(f"<li>{e(x)}</li>" for x in r.get("does_not_answer") or [])
    ev = "".join(f'<li id="ev-{e(f)}"><b>{e(re.sub(r"_[0-9]+$", "", f).replace("_", " "))}</b> <span class="b">{BASIS.get(v.get("basis"), ("rd",))[0]}</span>'
                 + (f'<div class="q">{e(v["quote"])}</div>' if v.get("quote") else f'<div class="d">{e(v.get("note") or "")}</div>')
                 + f'<div class="d"><a href="{e(r["sources"][v["src"]]["url"])}">{e(r["sources"][v["src"]]["url"])}</a> · read {e(r["sources"][v["src"]]["read"])} · saved copy sha256 <code>{e(r["sources"][v["src"]]["sha256"][:16])}…</code></div></li>'
                 for f, v in r["evidence"].items())
    rels = list(r.get("relations", [])) + [{"rel": "has_part", "target": x["slug"]} for x in ROWS if any(y["rel"] == "part_of" and y.get("target") == r["slug"] for y in x.get("relations", [])) and not any(z.get("target") == x["slug"] for z in r.get("relations", []))]
    groups = {}
    for x in rels: groups.setdefault(x["rel"], []).append(x)
    def item(x):
        if x.get("target"): return f'<li>{link(x["target"])}' + (f'<div class="d">{e(x["note"])}</div>' if x.get("note") else "") + "</li>"
        head = f'<a href="{e(x["url"])}">{e(x["label"])}</a>' if x.get("url") else e(x.get("label", ""))
        return f'<li>{head}<div class="d">{e(x.get("note") or "")}</div></li>'
    relhtml = "".join(f'<h3>{REL.get(k, k)}</h3><ul>{"".join(item(x) for x in v)}</ul>' for k, v in groups.items())
    inq = [q for q in QS if r["slug"] in [s["slug"] for s in q["resources"]]]
    qhtml = "".join(f'<li><a href="/aggregators/#q-{e(q["id"])}">{e(q["question"])}</a></li>' for q in inq)
    neg = "".join(f"<li>{e(t)}</li>" for t in r.get("negative_tags", []))
    src = "".join(f'<li><a href="{e(s["url"])}">{e(s["url"])}</a><div class="d">read {e(s["read"])} · HTTP {e(s["http"])} · sha256 <code>{e(s["sha256"][:16])}…</code></div></li>' for s in r["sources"].values())
    unc = "".join(f"<li>{e(u)}</li>" for u in r.get("unchecked", []))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(r["name"])} — Labor Vector meta-aggregator</title><meta name="description" content="{e(kernel(r))}"><link rel="canonical" href="{BASE}{r["slug"]}">
<meta name="citation_title" content="{e(r["name"])} — Labor Vector meta-aggregator record"><meta name="citation_editor" content="Lee Sharks"><meta name="citation_date" content="{D["compiled"]}"><meta name="citation_public_url" content="{BASE}{r["slug"]}">
<script type="application/ld+json">{jsonld(r)}</script>{HEAD}</head><body>{topbar("Labor and AI")}<div class="wrap">
<div class="crumb"><a href="/aggregators/">Labor Vector meta-aggregator</a> / {e(SHORT.get(r["intersections"][0], r["intersections"][0]))}</div><h1>{e(r["name"])}</h1>{chips(r)}<div class="kernel">{e(kernel(r))}</div>
<div class="act"><a class="btn" href="{e(r["url"])}">{("Its page ↗ (" + e(r["lifecycle"]["state"]) + ")") if r["lifecycle"]["state"] in ("ended", "paused") else ("Visit " + e(r["name"]) + " ↗")}</a>{''.join(f'<a class="btn ghost" href="{e(x["url"])}">The /non row</a>' for x in r.get("relations", []) if x["rel"] == "non_row")}<a class="btn ghost" href="/#dsl">The DSL audit</a><button class="btn ghost" type="button" data-copy="cite">Copy citation</button></div>
{ownq}
<h2>Who supplies, who directs, who gains</h2>{DIR}<p class="legend">Each as the resource itself records it. Where it records nothing, the census says so.</p>
<h2>What it records</h2><table>{tbl(REC)}</table><p class="legend">op the resource's own statement · 3p a third-party account · obs our observation · rd our reading. Hover a tag for its quote; each opens below with its source.</p>
<h2>What this evidence can settle</h2><div class="two"><div><h3>Can answer</h3><ul>{ans}</ul></div><div><h3>Cannot answer</h3><ul>{nans}</ul></div></div>
{f'<h3>In the worked questions</h3><ul>{qhtml}</ul>' if qhtml else ''}
<h2>Where it meets Labor Vector</h2><p class="rd"><span class="b">rd</span> {e(r.get("lv_intersection") or "none stated")}</p>
<h2>Entity</h2><table>{tbl(ENT)}</table>
<h2>Relations</h2>{relhtml or '<p class="pend">None recorded yet.</p>'}
<div style="margin-top:34px">{fold("Evidence", f'<ul class="ev">{ev}</ul>', len(r["evidence"]), "every field's quote, its source and the hash of the saved copy")}{fold("Negative tags", f'<ul>{neg}</ul>' if neg else '', len(r.get("negative_tags", [])), "what it is not")}{fold("Sources", f'<ul>{src}</ul>', len(r["sources"]), "every source read, with its date and hash")}{fold("Not yet checked", f'<ul>{unc}</ul>' if unc else '', len(r.get("unchecked", [])), "what remains to read")}</div>
<div style="margin-top:34px">{signup(r["slug"], r["name"])}</div><h2>Cite this record</h2><div class="cite"><p id="cite">{e(cite_text(r))}</p><p class="d">Record {BASE}{r["slug"]} · entity {BASE}{r["slug"]}#entity · <a href="/data/labor-census/census.json">the census as data</a></p></div><pre class="bib">{e(bibtex(r))}</pre>
<div class="foot">Editor: Lee Sharks (<a href="https://orcid.org/0009-0000-1599-0703">ORCID 0009-0000-1599-0703</a>). This page is the Labor Vector meta-aggregator's record of the resource above: its reading and fields are ours, and each field carries its source, its basis and the hash of the copy read. The resource's own terms and findings are kept as its own. Compiled {D["compiled"]}. CC BY 4.0.</div></div>
<script>document.querySelectorAll('[data-copy]').forEach(b=>b.onclick=()=>{{const t=document.getElementById(b.dataset.copy).innerText;(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(()=>{{const o=b.textContent;b.textContent='Copied';setTimeout(()=>b.textContent=o,1600)}}).catch(()=>{{}})}})</script>{SIGNUP_JS}</body></html>"""


SVG = lambda d: f'<svg viewBox="0 0 32 32" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>'
FLOW = [("supplies", "Who supplies the labor", "workers, users, writers, raters", '<circle cx="11" cy="11" r="4"/><circle cx="22" cy="12" r="3.2"/><path d="M4 25c1.2-4.4 4-6.6 7-6.6s5.8 2.2 7 6.6M17.5 24c.9-3.2 2.6-4.8 4.6-4.8s3.7 1.6 4.6 4.8"/>',
         "<b>Who supplies the labor</b>: annotators and moderators, platform and warehouse workers, writers whose work enters training, the people commissioning a system and correcting it. Each record says whose work its evidence is about."),
        ("directs", "Who directs it", "employer, platform, model, user", '<path d="M6 16h15"/><path d="M17 11l5 5-5 5"/><path d="M6 9v14"/>',
         "<b>Who directs it</b>: the employer, the platform, the vendor's software, the model, the user's commission. Where the direction is automated (hiring, scheduling, quotas, discipline) the record says by what."),
        ("gains", "Who receives its gains", "wages, credit, ownership, costs", '<path d="M6 22l6-6 5 5 9-11"/><path d="M20 10h6v6"/>',
         "<b>Who receives its gains</b>: wages and employment, workload, credit and ownership, and who bears the costs. A record states only what its resource measures or reports."),
        ("evidence", "On what evidence", "estimate, outcome, testimony, contract", '<rect x="7" y="6" width="18" height="20" rx="2"/><path d="M11 12h10M11 16h10M11 20h6"/>',
         "<b>On what evidence</b>: an exposure estimate, an observed employment outcome, a worker's testimony, a negotiated provision, a transcript of interactions, a rating against standards, a policy instrument. Each kind answers a different part of the question; the records keep them apart.")]


def index():
    inter = [i for i in INTER if any(i in r["intersections"] for r in ROWS)]
    kinds_used = [k for k in KINDS if any(k in r["evidence_kind"] for r in ROWS)]
    rows = "".join(f'<div class="row" data-int="{e(" ".join(r["intersections"]))}" data-kind="{e("|".join(r["evidence_kind"]))}" data-text="{e((r["name"] + " " + " ".join(r.get("aka", [])) + " " + r["operator"] + " " + kernel(r)).lower())}">'
                   f'<div class="n"><a href="{r["slug"]}">{e(r["name"])}</a></div>{chips(r)}<div class="k">{e(kernel(r))}</div><div style="margin-top:10px">{kinds(r)}</div></div>'
                   for r in sorted(ROWS, key=lambda r: r["name"].lower()))
    steps = '<span class="arrow" aria-hidden="true"></span>'.join(f'<button type="button" class="step" aria-expanded="false" aria-controls="x-{k}">{SVG(d)}<b>{t}</b><span>{u}</span></button>' for k, t, u, d, _ in FLOW)
    xs = "".join(f'<p id="x-{k}" class="x" hidden>{x}</p>' for k, _, _, _, x in FLOW)
    mat = "".join(f'<tr><td><a href="{r["slug"]}">{e(r["name"])}</a></td>' + "".join(f'<td>{"●" if k in r["evidence_kind"] else "<span class=d>·</span>"}</td>' for k in kinds_used) + "</tr>"
                  for r in sorted(ROWS, key=lambda r: r["name"].lower()))
    qs = "".join(f'<div class="qcard" id="q-{e(q["id"])}"><h3>{e(q["question"])}</h3><p>{e(q["why"])}</p><ul>'
                 + "".join(f'<li>{link(s["slug"])}<div class="d">{e(s["role"])}</div></li>' for s in q["resources"]) + "</ul>"
                 + (f'<p class="d">{e(q["gap"])}</p>' if q.get("gap") else "") + "</div>" for q in QS)
    btn = lambda key, vals, lab: "".join(f'<button data-{key}="{e(v)}">{e(lab(v))}</button>' for v in vals)
    ilist = "".join(f'<li><b>{e(SHORT[i])}</b>: {e(INTER[i].split(": ", 1)[1])}</li>' for i in INTER)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Labor and AI: the meta-aggregator — Labor Vector</title>
<meta name="description" content="The resources that observe the intersections of labor and AI, each formalized as an entity with sourced, dated fields: who supplies the labor, who directs it, who receives its gains, and on what evidence."><link rel="canonical" href="{BASE[:-1]}">{HEAD}</head><body>{topbar("Labor and AI")}<div class="wrap">
<div class="crumb"><a href="/">Labor Vector</a> / aggregators</div><h1>Labor and AI: the meta-aggregator</h1>
<div class="kernel">The resources that observe the intersections of labor and AI, from data workers' own inquiries and contract inventories to employment trackers and records of how people use AI systems, each formalized as an entity. Every record answers one question: {e(D["organizing_question"][0].lower() + D["organizing_question"][1:])} {len(ROWS)} resources, compiled {D["compiled"]}.</div>
<div class="flow" role="group" aria-label="The organizing question">{steps}</div><div class="flow-x">{xs}</div><noscript><style>.flow-x .x{{display:block!important}}</style></noscript>
<p class="fig-cap">An exposure estimate, an employment outcome, a worker's testimony, a negotiated protection and a record of interactions each show a different part of the same labor question. Tap a step for the fields that answer it.</p>
<h2>Five intersections</h2><ul class="ints">{ilist}</ul>
<div class="f"><button class="on" data-all="1">all</button>{btn("int", inter, lambda v: SHORT.get(v, v))}</div><div class="f">{btn("kind", kinds_used, lambda v: v)}</div>
<div id="L" class="grid">{rows}</div><p class="none" id="none">No resource matches.</p>
<h2 id="questions">Worked questions</h2><p class="section">A research question, the kind of evidence that can answer it, and the resources that hold that evidence.</p><div class="qs">{qs}</div>
<h2>Evidence by kind</h2><div class="tw"><table class="tv"><tr><td></td>{"".join(f"<td>{e(k)}</td>" for k in kinds_used)}</tr>{mat}</table></div>
<p class="legend">The census as data: <a href="/data/labor-census/census.json">census.json</a> and <a href="/data/labor-census/questions.json">questions.json</a>, with every saved source in <a href="https://github.com/leesharks000/laborvector/tree/main/data/labor-census/sources">data/labor-census/sources</a>.</p>
<div style="margin-top:34px">{signup()}</div><div class="foot">Labor Vector · laborvector.org · editor Lee Sharks (<a href="https://orcid.org/0009-0000-1599-0703">ORCID 0009-0000-1599-0703</a>) · a sibling of the <a href="https://www.machinemediation.org/aggregators/">MMRS meta-aggregator</a> and the <a href="https://www.provenanceerasure.org/aggregators/">provenance meta-aggregator</a></div></div>
<script>let fs={{}};const qi=document.querySelector('.srch input');qi.value=new URLSearchParams(location.search).get('q')||'';document.querySelector('.srch').onsubmit=ev=>{{ev.preventDefault();apply()}};qi.oninput=()=>apply();
function apply(){{const q=qi.value.trim().toLowerCase();let n=0;document.querySelectorAll('.f button').forEach(x=>{{const k=x.dataset.int?'int':x.dataset.kind?'kind':'all';x.classList.toggle('on',k==='all'?!fs.int&&!fs.kind:fs[k]===x.dataset[k])}});
document.querySelectorAll('#L .row').forEach(r=>{{const ok=(!fs.int||r.dataset.int.split(' ').includes(fs.int))&&(!fs.kind||r.dataset.kind.split('|').includes(fs.kind))&&(!q||q.split(' ').filter(Boolean).every(w=>r.dataset.text.includes(w)));r.style.display=ok?'':'none';n+=ok}});document.getElementById('none').style.display=n?'none':'block'}}
document.querySelectorAll('.f button').forEach(b=>b.onclick=()=>{{if(b.dataset.all){{fs={{}}}}else{{const k=b.dataset.int?'int':'kind',v=b.dataset[k];fs[k]=fs[k]===v?undefined:v}}apply()}});apply();
document.querySelectorAll('.flow .step').forEach(b=>b.onclick=()=>{{const on=b.getAttribute('aria-expanded')!=='true';document.querySelectorAll('.flow .step').forEach(x=>{{x.setAttribute('aria-expanded','false');document.getElementById(x.getAttribute('aria-controls')).hidden=true}});if(on){{b.setAttribute('aria-expanded','true');document.getElementById(b.getAttribute('aria-controls')).hidden=false}}}})</script>{SIGNUP_JS}</body></html>"""


EXTRA = """
/* Labor Vector additions (2026-10-29) */
.dir{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:0 0 6px}
.dir div{border:1px solid var(--border);background:var(--surface);border-radius:12px;padding:12px 14px}
.dir span{display:block;font-size:.74em;text-transform:uppercase;letter-spacing:.08em;color:var(--accent);font-weight:600;margin-bottom:4px}
.dir b{font-weight:500;font-size:.95em;line-height:1.45;display:block}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.two h3{margin-top:0}
.two ul,.qcard ul,.ints{padding-left:1.1em}
.rd{background:var(--soft);border:1px solid var(--border);border-radius:12px;padding:12px 14px}
.qs{display:grid;gap:12px}
.qcard{border:1px solid var(--border);background:var(--surface);border-radius:14px;padding:16px 18px}
.qcard h3{margin:0 0 6px;font-family:var(--serif);font-size:1.12em;font-weight:600}
.qcard p{font-size:.94em}
.qcard li{margin:6px 0}
.ints li{margin:4px 0}
.chip{white-space:normal;max-width:100%}
.act .btn{white-space:normal;max-width:100%;text-align:left}
"""

(ROOT / "assets").mkdir(exist_ok=True); (ROOT / "assets/lv.css").write_text(CSS + EXTRA, encoding="utf-8")
for _p, _t, _b in [("/privacy", "Privacy", PRIVACY), ("/subscribed", "Subscribed", "<p>You are on the list. Thank you.</p><p><a href=\"/aggregators/\">Back to the resources</a></p>")]:
    (ROOT / _p.strip("/")).mkdir(exist_ok=True); (ROOT / _p.strip("/") / "index.html").write_text(simple_page(_p, _t, _b), encoding="utf-8")
OUT.mkdir(exist_ok=True); (OUT / "index.html").write_text(index(), encoding="utf-8")
for r in ROWS:
    p = OUT / r["slug"]; p.mkdir(exist_ok=True); (p / "index.html").write_text(page(r), encoding="utf-8")
sm = ROOT / "sitemap.xml"; st = sm.read_text(encoding="utf-8")
add = "".join(f'  <url><loc>{u}</loc><lastmod>{D["compiled"]}</lastmod><priority>0.7</priority></url>\n' for u in [BASE[:-1]] + [BASE + r["slug"] for r in ROWS] if f"<loc>{u}</loc>" not in st)
sm.write_text(st.replace("</urlset>", add + "</urlset>"), encoding="utf-8")
lp = ROOT / "llms.txt"; lt = lp.read_text(encoding="utf-8")
blk = ("<!-- LABOR-AGGREGATOR-START -->\n## Labor and AI: the meta-aggregator\n\nThe resources that observe the intersections of labor and AI, each formalized as an entity with sourced, dated fields: "
       f"who supplies the labor, who directs it, who receives its gains, and on what evidence. {BASE[:-1]} (census as data: {SITE}/data/labor-census/census.json)\n\n"
       + "".join(f'- {r["name"]} ({r["kind"]}; {", ".join(SHORT.get(i, i) for i in r["intersections"])}; {", ".join(r["evidence_kind"])}): {BASE}{r["slug"]}\n' for r in sorted(ROWS, key=lambda r: r["name"].lower()))
       + "<!-- LABOR-AGGREGATOR-END -->\n")
lt = re.sub(r"<!-- LABOR-AGGREGATOR-START -->.*?<!-- LABOR-AGGREGATOR-END -->\n", lambda m: blk, lt, flags=re.S) if "LABOR-AGGREGATOR-START" in lt else lt.rstrip("\n") + "\n\n" + blk
lp.write_text(lt, encoding="utf-8")


def front_block():
    li = "".join(f'<a class="mini" href="/aggregators/{r["slug"]}"><b>{e(r["name"])}</b><span>{e(SHORT.get(r["intersections"][0]))} · {e(", ".join(r["evidence_kind"][:2]))}</span></a>' for r in sorted(ROWS, key=lambda r: r["name"].lower()))
    qli = "".join(f'<li><a href="/aggregators/#q-{e(q["id"])}">{e(q["question"])}</a></li>' for q in QS[:4])
    return ("<!-- LV-AGGREGATOR-START (generated by scripts/labor_aggregator/build.py from data/labor-census/census.json) -->\n"
            f'<section class="lvagg" id="labor-and-ai" aria-label="Labor and AI"><h2>Labor and AI: the meta-aggregator</h2><p class="lead">DSL asks where a system\'s labor flows relative to the task commissioned. The meta-aggregator widens the question to the labor around AI: '
            f'who supplies it, who directs it, and who receives its gains, and what kind of evidence each resource brings. {len(ROWS)} resources across five intersections, compiled {D["compiled"]}.</p>'
            f'<div class="minis">{li}</div><h3>Worked questions</h3><ul>{qli}</ul><p class="section" style="margin-top:12px"><a class="btn" href="/aggregators/">All {len(ROWS)} resources and every question</a> <a class="btn ghost" href="/data/labor-census/census.json">The census as data</a></p>' + signup() + SIGNUP_JS + '</section>\n'
            "<!-- LV-AGGREGATOR-END -->")


TOPBAR = "<!-- LV-TOPBAR-START (generated by scripts/labor_aggregator/build.py) -->" + topbar() + "<!-- LV-TOPBAR-END -->"
lp = ROOT / "index.html"; lt = lp.read_text(encoding="utf-8")
lt = re.sub(r"<!-- LV-TOPBAR-START.*?<!-- LV-TOPBAR-END -->", lambda m: TOPBAR, lt, count=1, flags=re.S) if "<!-- LV-TOPBAR-START" in lt else lt.replace("<!-- MSP-IDSTRIP-START -->", TOPBAR + "\n<!-- MSP-IDSTRIP-START -->", 1)
if "<!-- LV-AGGREGATOR-START" in lt:
    lt = re.sub(r"<!-- LV-AGGREGATOR-START.*?<!-- LV-AGGREGATOR-END -->", lambda m: front_block(), lt, count=1, flags=re.S)
elif "<!-- LV-AGGREGATOR-ANCHOR -->" in lt:
    lt = lt.replace("<!-- LV-AGGREGATOR-ANCHOR -->", front_block(), 1)
lp.write_text(lt, encoding="utf-8")
print(len(ROWS), "pages,", len(QS), "questions")
