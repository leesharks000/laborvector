# Brief: write labor census rows from saved sources (Labor Vector meta-aggregator, 2026-10-29)

Repository /home/claude/fleet/laborvector. Do not run git. Do not fetch anything: every source has already been fetched once and saved verbatim. Write only your rows, as new files data/labor-census/rows/<slug>.py, one per entity you are given.

## Read first
1. data/labor-census/census_src.py: the driver. It defines row(), Q(), the five intersections and the evidence kinds, the required fields, and the verbatim check.
2. The exemplar census this follows: /home/claude/fleet/provenance-erasure/data/provenance-census/census_src.py. Read three rows whole (iptc-metawatch, c2pa-conformance, olmotrace) for register: short field values, quotes carried in evidence, untested or unrecorded things said plainly, negative tags that keep the resource apart from what it is mistaken for.
3. Your entities' saved sources: data/labor-census/sources/<slug>--<id>.txt (the text) with sources/manifest.json (url, http, sha256). source-list.json says which ids belong to which entity. A source with http 403 or almost no text is unread; say so in unchecked, and never quote it.

## Each row (a single row(...) call in rows/<slug>.py)
- slug (given), name (the resource's own name), aka (its other names in its sources), url (its own canonical page), operator (who runs it, as its sources say), kind (what it is in its own words: database, tracker, dataset, index, rating programme, organisation, report series...).
- intersections: one or more keys of INTERSECTIONS, primary first, only where its sources make the resource bear on that intersection.
- evidence_kind: one or more of EVIDENCE_KINDS, for the kind of evidence it actually holds.
- unit: its own unit of record (a negotiated provision, a platform rating, a conversation mapped to a task, an occupation-month...).
- labor_object: whose labor, which work, as the sources say.
- direction: {"supplies": ..., "directs": ..., "gains": ...}: who supplies the labor, who directs it, who receives the gains or bears the costs, each only as the resource records or states it; "not recorded" where it does not. This is the census's organizing question; do not supply what the resource does not say.
- method (how it knows: survey, administrative payroll data, classified conversations, expert-graded tasks, worker-written inquiry, contract text...), coverage {"geography", "period"}, count {"value", "as_of"} where stated.
- findings: its headline findings as it states them, short, each figure backed by an evidence item. stated_limits: its own stated limits and caveats (quote them in evidence).
- answers / does_not_answer: two short lists of labor questions this resource's evidence can settle and cannot settle (e.g. "observed employment change by age and exposure" / "whether exposure causes the change"). These are readings; keep them exact to its method.
- lv_intersection: one or two sentences, the archive's reading, on where the resource meets Labor Vector's instruments (DSL: whether the system's labor advanced the commissioned task; task-origin; user labor drag; the directionality stack), or "none stated" where it does not. Keep the resource's terms intact; do not recast its findings in DSL's terms.
- data_access, license (as stated), lifecycle {"state": active | historical | paused | ended, "detail"}, founded where stated, version_and_time {"...": date, "read": "2026-10-29"}.
- negative_tags: "NOT ..." lines that keep it apart from what it is mistaken for or from a stronger claim than it makes.
- evidence: {field_key: Q("<slug>--<id>", "<verbatim quote>")}. Every figure, date, limit and self-description in the row is backed here. Quotes are verbatim from the saved .txt (the driver checks them, whitespace normalised). Use basis "third_party" in Q(...) for a source not the resource's own.
- relations: [{"rel": "neighbour" | "part_of" | "has_part" | "uses" | "used_by", "target": "<another slug in the census>", "note"}] only where the sources support it. The census slugs are in census_src.py ORDER.
- unchecked: what you could not read (unread sources, JavaScript applications, data not opened).

## Prose
Plain declarative English. Do not write "not X but Y", "X, not Y", "rather than" or "instead of" outside quotations; state the thing directly. No gendered generics. No hard line breaks inside values.

## Check
Run `cd data/labor-census && python3.12 census_src.py`. It prints problems for every row present; fix yours (missing fields, unknown keys, a quote not found) until your rows show none. Other readers' rows may appear; ignore their problems.

Final message: your rows, each with its intersections, evidence kinds and lifecycle; sources you could not use; anything a row could not record; and any resource whose sources make it look misplaced in this census.
