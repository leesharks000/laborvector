"""The labor census, first batch (2026-10-29). Writes census.json.

Operator, 2026-10-29: the meta-aggregator function implemented on Labor Vector, with pages, the research expanded; Labor Vector
focuses on the intersections of labor and AI. Organizing question (extending DSL's, "where does the system's labor flow relative
to your commission?"): who supplies the labor, who directs it, and who receives its gains, and what kind of evidence does each
resource bring to that question?

Each row is written in rows/<slug>.py from the saved sources only (sources/, dated and hashed in sources/manifest.json). Every
quoted value is checked verbatim (whitespace-normalised) against the saved text of its source. Fields without a quote are
readings, marked basis "reading". A resource's own terms and findings are kept as its own; where it meets Labor Vector's
instruments (DSL, task-origin, user labor drag) is stated separately, in lv_intersection, as the archive's reading.
"""
import json, pathlib, re
HERE = pathlib.Path(__file__).parent
MAN = json.load(open(HERE / "sources/manifest.json"))

INTERSECTIONS = {
    "labor-producing-ai": "Labor producing AI: annotation, moderation, evaluation, maintenance, and creative or scholarly work entering training and retrieval",
    "ai-governing-labor": "AI governing labor: hiring, surveillance, scheduling, quotas, evaluation and discipline",
    "labor-with-ai": "Labor performed with AI: assistance, delegation, task fidelity, correction burdens and user labor drag",
    "gains-and-losses": "Distribution of gains and losses: wages, employment, workload, credit, ownership, and who captures productivity gains",
    "worker-power": "Worker power: bargaining, organizing, consent, refusal, contestation and enforceable protections",
}
EVIDENCE_KINDS = ["exposure estimate", "observed employment outcome", "worker testimony", "negotiated provision", "interaction data",
                  "task benchmark", "rating against standards", "policy tracker", "product inventory", "data access", "organizing resource", "practitioner guidance"]


def Q(src, quote, basis="operator"):
    return {"src": src, "basis": basis, "quote": quote}


ROWS = []
def row(**r): ROWS.append(r)


ORDER = ["data-workers-inquiry", "fairwork-cloudwork", "pai-responsible-sourcing", "turkopticon",
         "coworker-bossware-database", "worker-info-exchange", "ilo-platform-policy-tracker",
         "anthropic-economic-index", "openai-gdpval", "microsoft-working-with-ai",
         "stanford-canaries", "yale-budget-lab-ai-tracker", "ilo-genai-exposure-index",
         "berkeley-negotiating-tech", "dair-luddite-lab"]
for slug in ORDER:
    p = HERE / "rows" / f"{slug}.py"
    if p.exists():
        exec(compile(p.read_text(encoding="utf-8"), str(p), "exec"), {"row": row, "Q": Q})

# ---------------------------------------------------------------- the archive's records of each entity (2026-10-29)
# its capture (the composition layer's account at its common name, seated in the Capture Registry with its dimensional PER)
# and its /non article, linked both ways (the /non pages link back by datasets/negative-of-the-negative/v2/panel/lv-records.json)
CAPTURE = {"data-workers-inquiry": "Data Workers' Inquiry", "fairwork-cloudwork": "Fairwork Cloudwork Ratings",
           "pai-responsible-sourcing": "Partnership on AI Responsible Sourcing", "turkopticon": "Turkopticon",
           "coworker-bossware-database": "Bossware and Employment Tech Database", "worker-info-exchange": "Worker Info Exchange",
           "ilo-platform-policy-tracker": "ILO Digital Labour Platform Policy Tracker", "anthropic-economic-index": "Anthropic Economic Index",
           "openai-gdpval": "GDPval", "microsoft-working-with-ai": "Microsoft Working with AI", "stanford-canaries": "Canaries in the Coal Mine",
           "yale-budget-lab-ai-tracker": "Yale Budget Lab AI labor market", "ilo-genai-exposure-index": "ILO Generative AI and Jobs index",
           "berkeley-negotiating-tech": "Negotiating Tech", "dair-luddite-lab": "Luddite Lab"}
HOMONYM = {"microsoft-working-with-ai": "Microsoft's own AI products and workforce", "stanford-canaries": "the idiom",
           "berkeley-negotiating-tech": "salary negotiation"}
for r in ROWS:
    q = CAPTURE.get(r["slug"])
    if not q:
        continue
    cslug = re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-") + "-aio-20261029"
    note = "the composition layer's account of the entity at its common name, signed out, seated in the Capture Registry with its dimensional PER"
    if r["slug"] in HOMONYM:
        note += f"; at this name the composition gives {HOMONYM[r['slug']]}, with the entity's own page as its first card"
    r.setdefault("relations", []).extend([
        {"rel": "capture", "url": f"https://www.alexanarch.org/captures/{cslug}/", "label": f"«{q}» on Google AI Overview, 2026-10-29",
         "note": note, "dates": {"observed": "2026-10-29"}},
        {"rel": "non_row", "url": f"https://www.alexanarch.org/non/{r['slug']}/", "label": "its /non article (EA-NEGONT-02 v0.9, equal case)",
         "note": "composed 2026-10-29 against its own pages, Wikipedia (no article), the capture's cards and the archive"}])

# ---------------------------------------------------------------- write
def norm(s): return re.sub(r"\s+", " ", s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')).strip()
problems = []
REQ = ["slug", "name", "url", "operator", "intersections", "evidence_kind", "kind", "unit", "labor_object", "direction", "method",
       "findings", "stated_limits", "answers", "does_not_answer", "lifecycle", "version_and_time", "negative_tags", "evidence"]
for r in ROWS:
    miss = [k for k in REQ if k not in r]
    if miss: problems.append((r.get("slug"), "missing fields", miss))
    for i in r.get("intersections") or []:
        if i not in INTERSECTIONS: problems.append((r["slug"], "unknown intersection", i))
    for k in r.get("evidence_kind") or []:
        if k not in EVIDENCE_KINDS: problems.append((r["slug"], "unknown evidence kind", k))
    srcs = {}
    for f, ev in r["evidence"].items():
        sid = ev["src"]
        if sid not in MAN:
            problems.append((r["slug"], f, "source not saved", sid)); continue
        srcs[sid] = {"url": MAN[sid]["url"], "read": MAN[sid]["fetched"][:10], "sha256": MAN[sid]["sha256"], "http": MAN[sid]["http"]}
        if ev.get("quote"):
            txt = norm((HERE / "sources" / f"{sid}.txt").read_text(encoding="utf-8"))
            if norm(ev["quote"]) not in txt:
                problems.append((r["slug"], f, sid, ev["quote"][:80]))
    r["sources"] = srcs
    r.setdefault("observed", {"on": "2026-10-29", "fetch": "read"})
unread = {k: {"url": v["url"], "http": v["http"], "fetched": v["fetched"]} for k, v in MAN.items() if v["http"] != "200" or v["text_chars"] < 100}
out = {"name": "Labor Vector meta-aggregator census", "compiled": "2026-10-29", "schema_version": "1.0", "editor": "Lee Sharks",
       "schema_note": ("The MMRS and provenance census core (slug, name, aka, url, operator, kind, unit, count, lifecycle, version_and_time, "
                       "negative_tags, evidence, relations, unchecked, sources) extended for labor: intersections (one or more of five), "
                       "evidence_kind, labor_object (whose work), direction (who supplies the labor, who directs it, who receives gains or bears costs, "
                       "each as the resource records it, or 'not recorded'), method, coverage, findings, stated_limits, answers and does_not_answer "
                       "(which labor questions this kind of evidence can and cannot settle), and lv_intersection (where it meets DSL, task-origin and "
                       "user labor drag: the archive's reading, kept apart from the resource's own terms). Every quote is verbatim from a saved source."),
       "organizing_question": "Who supplies the labor, who directs it, and who receives its gains — and what kind of evidence does this resource bring to that question?",
       "intersections": INTERSECTIONS, "evidence_kinds": EVIDENCE_KINDS, "unread_sources": unread, "rows": ROWS}
json.dump(out, open(HERE / "census.json", "w"), ensure_ascii=False, indent=1)
print(len(ROWS), "rows;", sum(len(r["evidence"]) for r in ROWS), "evidence items;", len(problems), "problems")
for p in problems: print("  ", p)
