#!/usr/bin/env python3
"""
Build raccolta_data/raccolta.json: the prayers of The Raccolta, authorized English translation (Ambrose St John;
London: Burns & Oates, 1910), each numbered entry with its section, title and text.

Source: archive.org's OCR, with each word's position (hOCR), of the University of St. Michael's College copy
(theraccoltaorcol00unknuoft), the only scan of this edition. The positions separate the Latin and English that the
book sets side by side. The indulgences each entry grants are left out: they were revised in 1968 (the Enchiridion
of Indulgences), and the site keeps the prayers. `--check` lists the words that aren't dictionary words, for review;
fixes go in FIXES.

Usage: ./venv/bin/python tools/raccolta/build.py [--check]
"""
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "library"))
sys.path.insert(0, str(ROOT / "tools" / "lives"))
from ocr import join_lines  # noqa: E402
from clean_butler import fix_word, is_word  # noqa: E402

CACHE = ROOT / "tools" / "library" / "cache" / "raccolta1910_hocr.html"
URL = "https://archive.org/download/theraccoltaorcol00unknuoft/theraccoltaorcol00unknuoft_hocr.html"
# archive.org's other OCR of the same scan, as plain text: it keeps some entry headings the first one lost
TEXT_CACHE = ROOT / "tools" / "library" / "cache" / "raccolta1910.txt"
TEXT_URL = "https://archive.org/download/theraccoltaorcol00unknuoft/theraccoltaorcol00unknuoft_djvu.txt"
OUT = ROOT / "raccolta_data" / "raccolta.json"

SECTIONS = ["ALMIGHTY GOD", "THE HOLY GHOST", "JESUS CHRIST", "THE CHILD JESUS", "THE BLESSED SACRAMENT",
            "JESUS CRUCIFIED", "THE PRECIOUS BLOOD", "THE SACRED HEART", "MARY", "MARY SORROWING", "MARY IMMACULATE",
            "THE HEART OF MARY", "THE ROSARY", "VARIOUS TITLES OF MARY", "THE HOLY ANGELS", "ST JOSEPH",
            "VARIOUS SAINTS", "THE FAITHFUL DEPARTED", "MISCELLANEOUS", "FOR STUDENTS"]


def section_name(s):
    small = {"of", "the"}
    words = s.lower().split()
    return " ".join(w if (k and w in small) else w.capitalize() for k, w in enumerate(words)).replace("St ", "St. ")


# A grant of indulgence, or the note that follows it
GRANT = re.compile(r"^(?:[ivxIVXl1!]{1,4}[.,]\s*)?(?:[\w]{1,5})?\s*(?:Days?|Years?|Quarantines?|Plenary|"
                   r"Indulgence)\b|^\(See Instructions|^\d{1,3},?\s*(?:Days|Years)")
# The rescripts cited at a page's foot: "14 Benedict XIII, January 15, 1728"
RESCRIPT = re.compile(r"^\d{1,3}\s+(?:Pius|Leo|Benedict|Clement|Gregory|Innocent|Alexander|Urban|Paul|Sixtus|"
                      r"S\.\s*C|Sacred|Rescr|Brief|Decr|Pr\.|Secr|Cong|Encycl|Ind|Rit|Mem)")
RUNNING = re.compile(r"^(?:[\dIlO]{1,3}\s+)?(" + "|".join(re.escape(s) for s in SECTIONS) +
                     r"|THE CONTENTS|INDEX|INSTRUCTIONS)\s*[\dIlO]{0,3}\s*$")
# The book's small capitals and the OCR's usual misreadings of them
FIXES = {"Gop": "GOD", "GoD": "GOD", "Gob": "GOD", "Gop's": "GOD'S", "Gop’s": "GOD’S", "LorD": "LORD", "Lorp": "LORD",
         "Lonp": "LORD", "LoRp": "LORD", "JEsus": "JESUS", "JEsu": "JESU", "JESUs": "JESUS", "JEsv": "JESU",
         "Curist": "CHRIST", "CunisT": "CHRIST", "Cunisr": "CHRIST", "CHnisT": "CHRIST", "CuristT": "CHRIST",
         "CurisT": "CHRIST", "Hoty": "HOLY", "Horv": "HOLY", "HoLy": "HOLY", "Guost": "GHOST", "Gnosr": "GHOST",
         "FarHER": "FATHER", "PArRI": "PATRI", "DEus": "DEUS", "DEo": "DEO", "DoMINUM": "DOMINUM", "Sow": "SON",
         "ezc": "etc", "efc": "etc", "ecc": "etc", "hrice": "thrice"}
DROP_CAP_ORDER = "MOAGHLIDTEBCSPRWVNJKFQUXYZ"


def _cached(path, url):
    if not path.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        path.write_bytes(urllib.request.urlopen(req, timeout=300).read())
    return path.read_text(encoding="utf-8")


def hocr():
    return _cached(CACHE, URL)


def text_stream():
    """The plain-text OCR as a stream of lines (its columns run together, so only its headings are used)."""
    out = []
    for line in _cached(TEXT_CACHE, TEXT_URL).split("\n"):
        s = re.sub(r"\s+", " ", line.strip())
        if s:
            run = RUNNING.match(s)
            out.append(("head", run.group(1)) if run else ("t", s, None))
    return out


def _letters(s, n=24):
    return re.sub(r"[^a-z]", "", s.lower())[:n]


def _start(it):
    return it[1] if it[0] == "t" else (it[1][0] if it[1] else it[2][0]) if it[0] == "p" else ""


def pages(text):
    """[[ {par, y, words: [(x0, x1, text)]} ]] per page, in reading order."""
    out = []
    for page in text.split('class="ocr_page"')[1:]:
        lines = []
        for par in re.split(r'<p class="ocr_par"', page)[1:]:
            pid = re.search(r'id="(par_[\d_]+)"', par).group(1)
            for line in re.split(r'<span class="ocr_line"', par)[1:]:
                y = int(re.search(r'title="bbox \d+ (\d+)', line).group(1))
                words = [(int(a), int(b), html.unescape(w)) for a, b, w in
                         re.findall(r'class="ocrx_word"[^>]*title="bbox (\d+) \d+ (\d+) \d+[^"]*"[^>]*>([^<]*)<', line)]
                if words:
                    lines.append({"par": pid, "y": y, "words": words})
        out.append(lines)
    return out


def split_at(words, col):
    """Left and right of the column gutter at x = col: the right column starts at a word at the gutter (or, for a
    drop capital's line, a little after it) with a gap before it."""
    for k in range(1, len(words)):
        x0, gap = words[k][0], words[k][0] - words[k - 1][1]
        if gap >= 15 and (abs(x0 - col) <= 22 or (col + 90 <= x0 <= col + 220 and words[k][2][:3].isupper())):
            return words[:k], words[k:]
    return None


LATIN = {"in", "et", "est", "me", "te", "per", "ad", "a", "de", "cum", "ut", "non", "pro", "sub", "qui", "quae",
         "nos", "tu", "tua", "tuam", "sancte", "pater", "gloria", "amen", "domine", "deus", "sit", "semper", "nobis"}


def english(words):
    """The share of a run of words that are English words: low for the Latin column, high for the English."""
    toks = [re.sub(r"[^A-Za-z]", "", w[2]).lower() for w in words]
    toks = [w for w in toks if len(w) > 1]
    return sum(1 for w in toks if is_word(w) and w not in LATIN) / len(toks) if toks else 0.5


def column(lines):
    """The x where a page's right-hand column (English beside Latin) begins, if it has one: the commonest start
    of a word after a wide gap in the middle of the page, found on at least three lines."""
    starts = []
    for ln in lines:
        w = ln["words"]
        for k in range(1, len(w)):
            if w[k][0] - w[k - 1][1] >= 45 and 800 <= w[k][0] <= 1150:
                starts.append(w[k][0])
    best, count = None, 0
    for s in starts:
        n = sum(1 for t in starts if abs(t - s) <= 30)
        if n > count:
            best, count = s, n
    return min(t for t in starts if abs(t - best) <= 30) if count >= 3 else None


def items(all_pages):
    """The book as a stream: ("t", text, par) for a line of one column, ("p", [latin lines], [english lines]) for a
    run of lines set side by side, ("head", section) for a running head, and ("page",) at each page break. Rescripts
    at a page's foot are dropped."""
    out = []
    for lines in all_pages:
        out.append(("page",))
        col = column(lines)
        rows = []  # (text, par, split or None)
        for k, ln in enumerate(lines):
            text = " ".join(w[2] for w in ln["words"]).strip()
            if k <= 1 and RUNNING.match(text):
                out.append(("head", RUNNING.match(text).group(1)))
                continue
            if RESCRIPT.match(text) or re.fullmatch(r"[\W\dIlO]{1,6}", text):
                continue
            heading = re.match(r"^[\dIlO\]]{1,3}[.,]\s+[A-Z]", text) or GRANT.match(text)
            sp = None
            if col and not heading:
                sp = split_at(ln["words"], col) or (([], ln["words"]) if ln["words"][0][0] >= col - 25 else None)
            rows.append((text, ln["par"], sp))
        # a run of lines split at the gutter is Latin beside English if, over the run, the left reads as Latin
        k = 0
        while k < len(rows):
            if rows[k][2] is None:
                out.append(("t", rows[k][0], rows[k][1]))
                k += 1
                continue
            j = k
            while j < len(rows) and rows[j][2] is not None:
                j += 1
            run = rows[k:j]
            lefts = [w for r in run for w in r[2][0]]
            rights = [w for r in run for w in r[2][1]]
            if sum(1 for r in run if r[2][0]) >= 2 and english(rights) - english(lefts) >= 0.2:
                out.append(("p", [" ".join(w[2] for w in r[2][0]) for r in run if r[2][0]],
                            [" ".join(w[2] for w in r[2][1]) for r in run]))
            else:
                out += [("t", r[0], r[1]) for r in run]
            k = j
    return out


def _first_words(raw):
    """An entry's first line of text in the plain-text OCR: where it begins in the positioned one."""
    for it in raw:
        if it[0] == "t" and len(re.sub(r"[^A-Za-z]", "", it[1])) >= 10 and not GRANT.match(it[1]) \
                and not RESCRIPT.match(it[1]) and not re.match(r"^\(?See Instr", it[1]):
            return it[1]
    return None


def aligned():
    """[{n, section, title, raw}]: the entries and titles found in the plain-text OCR (which keeps more headings),
    with their text from the positioned OCR (which keeps Latin and English apart). Each entry's first words are
    looked for in the positioned OCR, and of all the places they match, the longest chain in the book's order is
    kept."""
    from bisect import bisect_left
    from difflib import SequenceMatcher
    stream = items(pages(hocr()))
    found = entries(text_stream())
    keys = {}
    starts = {}
    for k, it in enumerate(stream):
        if it[0] in ("t", "p"):
            for s in {_start(it)} | ({it[2][0]} if it[0] == "p" and it[1] else set()):
                ls = _letters(s, 16)
                starts.setdefault(k, []).append(ls)
                for o in (1, 2, 3):  # a drop capital lost in either OCR shifts the letters by one
                    keys.setdefault(ls[o:o + 4], set()).add(k)
    hits = []  # (entry index, stream index)
    for i, e in enumerate(found):
        first = _first_words(e["raw"])
        if not first:
            continue
        a = _letters(first, 16)
        cands = set().union(*(keys.get(a[o:o + 4], set()) for o in (1, 2, 3)))
        for k in sorted(cands):
            if any(SequenceMatcher(None, a, s).ratio() >= 0.8 for s in starts[k]):
                hits.append((i, k))
    # the positioned OCR's own headings, where it kept them, are places too
    by_n = {e["n"]: i for i, e in enumerate(found)}
    own = {}
    for e in entries(stream):
        if e["n"] in by_n:
            hits.append((by_n[e["n"]], e["at"]))
        else:  # an entry only the positioned OCR has
            found.append({**e, "raw": []})
            by_n[e["n"]] = len(found) - 1
            hits.append((by_n[e["n"]], e["at"]))
    order = sorted(range(len(found)), key=lambda i: found[i]["n"])
    rank = {i: r for r, i in enumerate(order)}
    hits = [(rank[i], k) for i, k in hits]
    found = [found[i] for i in order]
    # the longest chain increasing in both entry and position (patience sorting)
    hits = sorted(set(hits), key=lambda h: (h[0], -h[1]))
    tails, prev, idx = [], {}, []
    for h in hits:
        j = bisect_left(tails, h[1])
        if j == len(tails):
            tails.append(h[1]); idx.append(h)
        else:
            tails[j] = h[1]; idx[j] = h
        prev[h] = idx[j - 1] if j else None
    chain, h = [], idx[-1] if idx else None
    while h:
        chain.append(h)
        h = prev[h]
    chain.reverse()
    out = []
    for c, (i, k) in enumerate(chain):
        end = chain[c + 1][1] if c + 1 < len(chain) else len(stream)
        raw = list(stream[k:end])
        nxt = found[chain[c + 1][0]] if c + 1 < len(chain) else None
        # the next entry's heading and grants end this one's span
        while raw and (raw[-1][0] in ("page", "head") or (raw[-1][0] == "t" and (
                GRANT.match(raw[-1][1]) or re.match(r"^\(?See Instr", raw[-1][1])
                or (nxt and SequenceMatcher(None, _letters(raw[-1][1], 30), _letters(nxt["title"], 30)).ratio() > 0.6)
                or re.match(r"^\S{1,4}[.,]\s+[A-Z]", raw[-1][1])))):
            raw.pop()
        e = found[i]
        # and this entry's own heading and grants, where the span begins at them
        while raw and (raw[0][0] in ("page", "head") or (raw[0][0] == "t" and (
                GRANT.match(raw[0][1]) or re.match(r"^\(?See Instr", raw[0][1])
                or re.match(r"^[\dIlO\]]{1,3}[.,]\s+[A-Z]", raw[0][1])
                or SequenceMatcher(None, _letters(raw[0][1], 30), _letters(e["title"], 30)).ratio() > 0.6))):
            raw.pop(0)
        out.append({"n": e["n"], "section": e["section"], "title": e["title"], "raw": raw})
    return out


def fix(tok):
    core = re.sub(r"^[^\w]+|[^\w']+$", "", tok)
    if core in FIXES:
        return tok.replace(core, FIXES[core])
    return fix_word(tok, [])


def drop_cap(word):
    """The capital the OCR lost from a prayer's first word ("Y GOD" for "MY GOD"), if adding one makes a word."""
    core = re.sub(r"[^A-Za-z]", "", word)
    if not core or (len(core) > 2 and is_word(core.lower())):
        return word
    for c in DROP_CAP_ORDER:
        if is_word((c + core).lower()):
            return c + word
    return word


def tidy(text, first=True):
    toks = [fix(t) for t in re.sub(r"\s+", " ", text).strip().split(" ")]
    if first and toks and re.match(r"^[A-Z]{1,6}[,!]?$", toks[0]) and len(toks) > 1:
        toks[0] = drop_cap(toks[0])
    s = " ".join(toks)
    s = re.sub(r"\s+([,;:.!?])", r"\1", s)
    s = re.sub(r"\*\*\s*|‘‘\s*", "“", s).replace(" ”", "”")
    return s


def entries(stream):
    """[{n, section, title, parts}]: walking the numbers in order, an entry begins with the next number and a title,
    followed within a few lines by its grant of indulgence."""
    out, section, expect = [], None, 1
    begun = False  # the book's numbered instructions come first; the prayers begin with the Trisagion
    texts = [(k, it) for k, it in enumerate(stream) if it[0] == "t"]
    pos = {k: j for j, (k, _) in enumerate(texts)}
    skip_until = -1
    for k, it in enumerate(stream):
        if it[0] == "head":
            if it[1] in SECTIONS:
                section = it[1]
            elif it[1] in ("THE CONTENTS", "INDEX") and out:
                break
            continue
        if k <= skip_until or it[0] == "page":
            continue
        if it[0] == "t" and not begun:
            begun = bool(re.match(r"^[\]1Il][.,]\s+The Angelic Trisagion", it[1]))
            if not begun:
                continue
        if it[0] == "t":
            m = re.match(r"^([\dIlO\]]{1,3})[.,]\s+(.+)$", it[1])
            num = None
            if m:
                try:
                    num = int(m.group(1).replace("I", "1").replace("l", "1").replace("O", "0").replace("]", "1"))
                except ValueError:
                    pass
            if num is not None and expect <= num <= expect + 15 and re.match(r"[A-Z‘'“\"(]", m.group(2)):
                after = [t for _, t in texts[pos[k] + 1:pos[k] + 7]]
                # a few numbers may be misread or missing: a longer jump needs the grant right after the title
                # the exact next number with a short title needs no grant (some entries have none: the Stations)
                titled = num == expect and expect > 12 and len(m.group(2)) <= 70 and m.group(2).rstrip().endswith(".")
                if titled or any(GRANT.match(t[1]) for t in after[:5 if num <= expect + 4 else 2]):
                    title = [m.group(2)]
                    last = k
                    for kk, t in texts[pos[k] + 1:pos[k] + 7]:
                        if GRANT.match(t[1]):
                            break
                        title.append(t[1])
                        last = kk
                    skip_until = last
                    out.append({"n": num, "section": section, "title": join_lines(title), "raw": [], "at": k})
                    expect = num + 1
                    continue
        if out:
            out[-1]["raw"].append(it)
    return out


def parts(raw):
    """An entry's text: [{"en": [...], "la": [...]}] for prayers, {"note": "..."} for the book's directions. Grants
    of indulgence, and directions about gaining them, are left out."""
    out, cur, par = [], [], None

    def flush():
        nonlocal cur
        if cur:
            text = tidy(join_lines(cur))
            if out and "note" in out[-1] and re.match(r"^[a-z]", text):  # runs on over a page break
                out[-1]["note"] = join_lines([out[-1]["note"], text])
            else:
                out.append({"note": text})
        cur = []

    for it in raw:
        if it[0] in ("page", "head"):
            continue
        if it[0] == "p":
            flush()
            la, en = tidy(join_lines(it[1])), tidy(join_lines(it[2]))
            if out and "en" in out[-1] and re.match(r"^[a-z]", en):  # the pair runs on from the previous page
                out[-1]["en"][-1] = join_lines([out[-1]["en"][-1], en])
                if la:
                    out[-1]["la"][-1] = join_lines([out[-1]["la"][-1], la]) if out[-1]["la"] else la
            else:
                out.append({"en": [en], "la": [la] if la else []})
            continue
        if GRANT.match(it[1]):
            flush()
            continue
        if it[2] != par:
            flush()
            par = it[2]
        cur.append(it[1])
    flush()
    keep = []
    for p in out:
        if "note" in p and re.search(r"\b(?:Indulgences?|indulgenced|Plenary|S\.\s?C\.|Rescript)\b", p["note"]):
            continue  # how to gain the indulgences, now revised
        keep.append(p)
    return keep


def slugify(s):
    s = re.sub(r"[“”‘’\"']", "", s.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:70].rstrip("-")


def build():
    data = []
    for e in aligned():
        title = tidy(re.sub(r"\s+", " ", e["title"]), first=False).rstrip(".")
        data.append({"n": e["n"], "section": section_name(e["section"] or ""), "title": title,
                     "slug": f"{e['n']}-{slugify(title)}", "parts": parts(e["raw"])})
    return data


def check(data):
    from collections import Counter
    bad = Counter()
    for e in data:
        for p in e["parts"]:
            for w in re.findall(r"[A-Za-z]+", " ".join(p.get("en", [])) + " " + p.get("note", "")):
                if len(w) > 2 and not is_word(w.lower()) and not w.isupper():
                    bad[w] += 1
    nums = [e["n"] for e in data]
    print(len(data), "entries; missing numbers:", sorted(set(range(1, max(nums) + 1)) - set(nums)))
    print("no text:", [e["n"] for e in data if not e["parts"]])
    print(len(bad), "non-words:", ", ".join(f"{w}×{n}" for w, n in bad.most_common(200)))


if __name__ == "__main__":
    data = build()
    if "--check" in sys.argv:
        check(data)
    else:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Wrote {OUT.relative_to(ROOT)}: {len(data)} entries")
