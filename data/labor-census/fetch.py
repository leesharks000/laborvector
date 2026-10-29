"""Fetch each source once, verbatim: <id>.html.gz (the raw bytes, gzipped; sha256 is of the raw bytes) and <id>.txt (scripts and styles stripped, words kept).
manifest.json records url, final url, HTTP code, fetch time (UTC) and sha256 of the raw bytes."""
import json, subprocess, hashlib, html, re, sys, datetime, pathlib, os
HERE = pathlib.Path(__file__).parent / "sources"
SRC = json.load(open(pathlib.Path(__file__).parent / "source-list.json"))
man_p = HERE / "manifest.json"
man = json.load(open(man_p)) if man_p.exists() else {}
def text_of(b, ctype, path):
    if b[:4] == b"%PDF":
        r = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True)
        return r.stdout.decode("utf-8", "replace")
    t = b.decode("utf-8", "replace")
    # HTML by its content type, or by its markup near the head (repair 2026-10-29: the ILO paper's page opens with a <script>
    # block, so "<html" was not in its first 2,000 characters and its saved text was the raw HTML)
    head = t[:20000].lower()
    if "html" not in (ctype or "").lower() and not any(m in head for m in ("<html", "<!doctype", "<head", "<body", "<script")):
        return t
    t = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", t)
    t = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h[1-6]|tr|td|th|section|article|blockquote|dd|dt)>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n\n", t).strip()
for ent, items in SRC.items():
    for sid, url in items.items():
        key = f"{ent}--{sid}"
        if key in man and "--refetch" not in sys.argv: continue
        out = HERE / f"{key}.html"
        r = subprocess.run(["curl", "-sSL", "-m", "120", "-A", "Mozilla/5.0 (compatible; Labor-Vector-census)", "-o", str(out), "-w", "%{http_code} %{url_effective} %{content_type}", url], capture_output=True, text=True)
        code, final, ctype = (r.stdout.split(" ", 2) + ["", "", ""])[:3]
        b = out.read_bytes() if out.exists() else b""
        txt = text_of(b, ctype, out) if b else ""
        (HERE / f"{key}.txt").write_text(txt, encoding="utf-8")
        man[key] = {"entity": ent, "id": sid, "url": url, "final_url": final, "http": code, "content_type": ctype,
                    "fetched": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b), "text_chars": len(txt), "error": r.stderr.strip()[:200]}
        if out.exists():
            import gzip, shutil
            with open(out, "rb") as fi, gzip.GzipFile(str(out) + ".gz", "wb", mtime=0) as fo: shutil.copyfileobj(fi, fo)
            out.unlink()
        print(key, code, len(b), len(txt))
json.dump(man, open(man_p, "w"), indent=1)
