#!/usr/bin/env python3
"""
Two-way translator: English <-> cuneiform (Unicode, block U+12000...).

Three modes (--mode):
  logograms  Sumerian logograms from the dictionary only; words that are not
             in the dictionary are kept as-is in ⟨angle brackets⟩, so nothing
             is lost.
  translit   The English text is spelled out in syllabic signs (CV, VC, CVC;
             missing syllables are built from several signs). Word order and
             function words are preserved.
  hybrid     Logograms where the word is in the dictionary (with Sumerian
             grammar: SOV order, adjective after the noun), syllabic spelling
             for everything else. Syllabic words start with the marker
             U+12470 so that they can be told apart when translating back.

Examples:
  python cuneiform.py "The great king gave bread to the people"
  python cuneiform.py --mode translit "Kingdom of Ukraine"
  python cuneiform.py --mode hybrid --explain "King David saw 3 cities"
  python cuneiform.py "𒈗 𒃲 𒉒 𒀭"          # cuneiform -> English
  python cuneiform.py                         # interactive mode (:mode translit)
"""
import re
import sys
import argparse
import unicodedata

from _dict import LEXICON, NUM_WORDS, STOPWORDS, IRREGULAR, IRREG_PLURAL

MODES = ("logograms", "translit", "hybrid")
MARK = chr(0x12470)   # marks a syllabic (phonetic) word in hybrid mode


def _sign(name):
    try:
        return unicodedata.lookup("CUNEIFORM SIGN " + name)
    except KeyError:
        return None


def _signs(spec):
    out = ""
    for name in spec.split("+"):
        ch = _sign(name.strip())
        if ch is None:
            return None
        out += ch
    return out


# --- logogram tables ----------------------------------------------------------
EN = {}      # English word -> (reading, signs, pos)
LOGO = {}    # signs -> [(gloss, pos, reading), ...]
MISSING = []  # sign specs from the dictionary that Unicode does not have
for _line in LEXICON.strip().splitlines():
    _words, _reading, _spec, _pos = [p.strip() for p in _line.split("|")]
    _chars = _signs(_spec)
    if _chars is None:
        MISSING.append(_spec)
        continue
    _gl = _words.split(",")
    for _w in _gl:
        EN.setdefault(_w, (_reading, _chars, _pos))
    LOGO.setdefault(_chars, []).append((_gl[0], _pos, _reading))

# --- syllabary: V, CV, VC, CVC (built from Unicode sign names) ----------------
CONS = "bdghklmnprsštz"
VOWELS = "aeiu"
SYLL = {}       # reading -> sign
SYL_REV = {}    # sign -> reading


def _cname(c):
    return "SH" if c == "š" else c.upper()


def _reg(reading, name):
    ch = _sign(name)
    if ch:
        SYLL[reading] = ch
        SYL_REV.setdefault(ch, reading)


for _v in VOWELS:
    _reg(_v, _v.upper())
for _c in CONS:
    for _v in VOWELS:
        _reg(_c + _v, _cname(_c) + _v.upper())
        _reg(_v + _c, _v.upper() + _cname(_c))
for _c1 in CONS:
    for _v in VOWELS:
        for _c2 in CONS:
            _reg(_c1 + _v + _c2, _cname(_c1) + _v.upper() + _cname(_c2))

DIS, TEN = _sign("DISH"), _sign("U")      # the signs for 1 and 10
EQ = {"b": "bp", "p": "pb", "d": "dt", "t": "td", "g": "gk", "k": "kg"}
VOWEL_ALT = {"a": "a", "e": "ei", "i": "ie", "u": "u"}


def _alts(c):
    return list(EQ.get(c, c)) if c else [""]


def find(c1, v, c2=""):
    """Find a sign for a syllable; voiced/voiceless consonants and e/i are
    interchangeable (as in Hurrian-style cuneiform spelling)."""
    for a in _alts(c1):
        for w in VOWEL_ALT.get(v, v):
            for b in _alts(c2):
                if a + w + b in SYLL:
                    return a + w + b
    return None


# --- phonetics ----------------------------------------------------------------
def to_phonemes(word):
    w = word.lower()
    for a, b in [("tch", "k"), ("ch", "k"), ("sh", "š"), ("th", "t"),
                 ("ph", "p"), ("ck", "k"), ("qu", "ku"), ("wh", "u"),
                 ("ng", "n"), ("gh", ""), ("x", "ks")]:
        w = w.replace(a, b)
    w = re.sub(r"c(?=[eiy])", "s", w)
    w = w.translate(str.maketrans({"c": "k", "q": "k", "v": "b", "f": "p",
                                   "w": "u", "y": "i", "j": "g", "o": "u"}))
    if len(w) > 3:
        w = re.sub(r"(?<=[^aeiu])e$", "", w)          # silent final -e
    return re.sub(r"(.)\1+", r"\1", w)


def _lone(c, prev_v, next_v):
    """A consonant without a vowel of its own: combine it with a neighbouring vowel."""
    if prev_v:
        r = find("", prev_v, c)
        if r:
            return r
    return find(c, next_v or "i") or find(c, "u") or find(c, "a")


def syllabify(ph):
    out, i, n = [], 0, len(ph)

    def isv(k):
        return k < n and ph[k] in VOWELS

    def last_vowel():
        src = out[-1] if out else ""
        return next((ch for ch in reversed(src) if ch in VOWELS), "")

    while i < n:
        c = ph[i]
        if c in VOWELS:
            out.append(find("", c) or c)
            i += 1
            continue
        if isv(i + 1):
            v = ph[i + 1]
            if i + 2 < n and not isv(i + 2) and not isv(i + 3):
                r = find(c, v, ph[i + 2])               # CVC
                if r:
                    out.append(r)
                    i += 3
                    continue
            r = find(c, v)                               # CV
            if r:
                out.append(r)
                i += 2
                continue
        r = _lone(c, last_vowel(), ph[i + 1] if isv(i + 1) else "")
        if r:
            out.append(r)
        i += 1
    return out


def spell(word):
    reads = syllabify(to_phonemes(re.sub(r"[^A-Za-z]", "", word)))
    return "".join(SYLL.get(r, "") for r in reads), reads


def join_readings(reads):
    s = ""
    for r in reads:
        if s and len(r) >= 2 and r[0] in VOWELS and r[1] not in VOWELS and s[-1] == r[0]:
            s += r[1:]                                  # ki + in -> kin
        else:
            s += r
    return s


# --- English -> cuneiform -----------------------------------------------------
def lemma_candidates(w):
    if w in IRREGULAR:
        yield IRREGULAR[w], w in ("children", "men", "women")
    yield w, False
    if w.endswith("ies"):
        yield w[:-3] + "y", True
    if w.endswith("es"):
        yield w[:-2], True
    if w.endswith("s"):
        yield w[:-1], True
    for suf in ("ing", "ed"):
        if w.endswith(suf):
            b = w[:-len(suf)]
            yield b, False
            yield b + "e", False
            if len(b) > 2 and b[-1] == b[-2]:
                yield b[:-1], False


def number_signs(n):
    return TEN * (n // 10) + DIS * (n % 10)


def reorder(clause):
    # 1) noun phrases: adjectives move after their noun
    units, pending = [], []
    for t in clause:
        if t["pos"] == "adj":
            pending.append(t)
        elif t["pos"] == "n":
            units.append([t] + pending)
            pending = []
        else:
            units += [[a] for a in pending] + [[t]]
            pending = []
    units += [[a] for a in pending]
    # 2) possession: king's palace -> palace king
    i = 0
    while i < len(units) - 1:
        if units[i][0].get("poss"):
            units[i], units[i + 1] = units[i + 1], units[i]
            i += 2
        else:
            i += 1
    c = [t for u in units for t in u]
    # 3) verb (together with a negation) goes to the end
    body, tail, i = [], [], 0
    while i < len(c):
        if c[i]["pos"] == "neg" and i + 1 < len(c) and c[i + 1]["pos"] == "v":
            tail += [c[i], c[i + 1]]
            i += 2
        elif c[i]["pos"] == "v":
            tail.append(c[i])
            i += 1
        else:
            body.append(c[i])
            i += 1
    return body + tail


def en_to_cu(text, mode="hybrid", explain=False):
    toks = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+|[.!?;:,]", text)
    translit = mode == "translit"
    lines, clause, report = [], [], []

    def flush():
        nonlocal clause
        if clause:
            seq = clause if translit else reorder(clause)
            lines.append(" ".join(t["cu"] for t in seq))
        clause = []

    def phonetic(word, note):
        chars, reads = spell(word)
        if not chars:
            return
        cu = chars if translit else MARK + chars
        clause.append({"cu": cu, "pos": "name"})
        report.append((word, "-".join(reads), cu, note))

    for tok in toks:
        if tok in ".!?;:,":
            flush()
            continue
        poss = tok.lower().endswith("'s")
        word = tok[:-2] if poss else tok.split("'")[0]
        low = word.lower()
        if word.isdigit():
            n = int(word)
            if 0 < n < 60:
                clause.append({"cu": number_signs(n), "pos": "num"})
                report.append((word, "—", number_signs(n), "number"))
            else:
                clause.append({"cu": "⟨" + word + "⟩", "pos": "name"})
                report.append((word, "—", "⟨" + word + "⟩", "number outside 1-59 (kept)"))
            continue
        if translit:
            phonetic(word, "transliteration")
            continue
        if low == "and":
            flush()
            report.append((word, "—", "", "separates clauses"))
            continue
        if low in NUM_WORDS:
            cu = number_signs(NUM_WORDS[low])
            clause.append({"cu": cu, "pos": "num"})
            report.append((word, "—", cu, "numeral"))
            continue
        if low in STOPWORDS:
            report.append((word, "—", "", "function word, skipped"))
            continue
        hit = next(((EN[l], pl) for l, pl in lemma_candidates(low) if l in EN), None)
        if hit:
            (reading, chars, pos), plural = hit
            cu = chars * 2 if plural and pos == "n" else chars
            clause.append({"cu": cu, "pos": pos, "poss": poss})
            report.append((word, reading + ("×2" if cu != chars else ""), cu, "logogram"))
        elif mode == "logograms":
            clause.append({"cu": "⟨" + word + "⟩", "pos": "name", "poss": poss})
            report.append((word, "—", "⟨" + word + "⟩", "not in dictionary (kept)"))
        else:
            n0 = len(clause)
            phonetic(word, "syllabic spelling (not in dictionary)")
            if poss and len(clause) > n0:
                clause[-1]["poss"] = True
    flush()
    result = "\n".join(lines)
    if explain:
        result += "\n\n" + "\n".join(
            f"{w:<12} {r:<16} {c:<10} {n}" for w, r, c, n in report)
    return result


# --- cuneiform -> English -----------------------------------------------------
def is_cuneiform(ch):
    return 0x12000 <= ord(ch) <= 0x1254F


def pluralize(w):
    if w in IRREG_PLURAL:
        return IRREG_PLURAL[w]
    if w.endswith("y") and w[-2:-1] not in ("a", "e", "i", "o", "u"):
        return w[:-1] + "ies"
    if w.endswith(("s", "x", "ch", "sh")):
        return w + "es"
    return w + "s"


def pick(chars, is_last):
    options = LOGO[chars]
    verbs = [o for o in options if o[1] == "v"]
    others = [o for o in options if o[1] != "v"]
    return verbs[0] if (is_last and verbs) else (others or verbs)[0]


def decode_logograms(s, is_last):
    h = len(s) // 2
    if len(s) % 2 == 0 and s[:h] == s[h:] and s[:h] in LOGO:     # reduplication = plural
        g, pos, r = pick(s[:h], False)
        return (pluralize(g) if pos == "n" else g, pos, r + "×2")
    parts, i = [], 0
    while i < len(s):
        for size in (3, 2, 1):
            seg = s[i:i + size]
            if len(seg) == size and seg in LOGO:
                parts.append(seg)
                i += size
                break
        else:
            return None
    picks = [pick(p, is_last and k == len(parts) - 1) for k, p in enumerate(parts)]
    return ("-".join(p[0] for p in picks), picks[-1][1], "-".join(p[2] for p in picks))


def decode_word(word, mode, is_last):
    if word.startswith("⟨") and word.endswith("⟩"):
        return (word[1:-1], "name", "")
    chars = [c for c in word if is_cuneiform(c) and c != MARK]
    if not chars:
        return None
    forced = mode == "translit" or word.startswith(MARK)
    if not forced:
        if all(c in (DIS, TEN) for c in chars):
            return (str(chars.count(TEN) * 10 + chars.count(DIS)), "num", "")
        r = decode_logograms("".join(chars), is_last)
        if r:
            return r
        if mode == "logograms":
            return ("?", "name", "")
    reads = [SYL_REV.get(c) or (LOGO[c][0][2] if c in LOGO else "?") for c in chars]
    text = join_readings(reads).replace("š", "sh")
    return (text if mode == "translit" else "‹" + text + "›", "name", "-".join(reads))


def cu_to_en(text, mode="hybrid", explain=False):
    out, report = [], []
    for line in text.splitlines():
        words = [w for w in line.split()
                 if any(is_cuneiform(c) for c in w) or (w.startswith("⟨") and w.endswith("⟩"))]
        dec = []
        for i, w in enumerate(words):
            d = decode_word(w, mode, i == len(words) - 1)
            if d:
                dec.append(list(d))
                report.append((w, d[2], d[0], d[1]))
        if mode != "translit":
            tail, rest, i = [], [], 0
            while i < len(dec):                       # SOV -> SVO
                if dec[i][1] == "neg" and i + 1 < len(dec) and dec[i + 1][1] == "v":
                    tail += [dec[i], dec[i + 1]]
                    i += 2
                elif dec[i][1] == "v":
                    tail.append(dec[i])
                    i += 1
                else:
                    rest.append(dec[i])
                    i += 1
            if tail:
                pos = next((k for k, d in enumerate(rest) if d[1] in ("n", "name", "pron")),
                           len(rest) - 1)
                end = pos + 1
                while end < len(rest) and rest[end][1] == "adj":
                    end += 1
                rest[end:end] = tail
            dec = rest
            i = 1
            while i < len(dec):                       # noun+adjective -> adjective+noun
                if dec[i][1] == "adj" and dec[i - 1][1] in ("n", "name"):
                    dec[i - 1], dec[i] = dec[i], dec[i - 1]
                i += 1
        out.append(" ".join(d[0] for d in dec))
    result = "\n".join(out)
    if explain:
        result += "\n\n" + "\n".join(f"{w:<10} {r:<16} {g:<14} {p}" for w, r, g, p in report)
    return result


def translate(text, mode="hybrid", explain=False):
    """Direction is detected automatically: cuneiform in -> English out, and vice versa."""
    if any(is_cuneiform(c) for c in text):
        return cu_to_en(text, mode, explain)
    return en_to_cu(text, mode, explain)


def _mode_arg(value):
    value = value.lower()
    if value not in MODES:
        raise argparse.ArgumentTypeError("mode must be one of: " + ", ".join(MODES))
    return value


def main():
    for stream in (sys.stdout, sys.stdin):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="English <-> cuneiform translator")
    ap.add_argument("text", nargs="*")
    ap.add_argument("--mode", type=_mode_arg, default="hybrid",
                    help="logograms | translit | hybrid (default: hybrid)")
    ap.add_argument("--explain", action="store_true", help="show a word-by-word breakdown")
    args = ap.parse_args()
    mode = args.mode
    if args.text:
        print(translate(" ".join(args.text), mode, args.explain))
        return
    print(f"Mode: {mode}. Enter text (':mode translit' to switch mode, empty line to quit).")
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break
        if not line:
            break
        if line.startswith(":mode"):
            try:
                mode = _mode_arg(line.split(maxsplit=1)[1])
                print("Mode:", mode)
            except (IndexError, argparse.ArgumentTypeError):
                print("Modes:", ", ".join(MODES))
            continue
        print(translate(line, mode, args.explain))


if __name__ == "__main__":
    main()
