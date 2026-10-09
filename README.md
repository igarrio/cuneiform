# Cuneiform Translator

A small, dependency-free Python tool that translates **English ⇄ cuneiform** (Unicode block U+12000–U+1254F).
The direction is detected automatically: if the input contains cuneiform signs it is translated to English, otherwise to cuneiform.

Cuneiform is a writing system, not a single language, so the translator targets **Sumerian**: words become Sumerian logograms (one sign ≈ one word) where possible, and are spelled out with syllabic signs otherwise.

## Requirements

- Python 3.8+
- A font with cuneiform glyphs to see the output (e.g. *Segoe UI Historic* on Windows 10+, *Noto Sans Cuneiform* elsewhere)

## Usage

```bash
python cuneiform.py "The great king gave bread to the people"
python cuneiform.py --mode translit "Kingdom of Ukraine"
python cuneiform.py --mode hybrid --explain "King David saw 3 cities"
python cuneiform.py "𒈗 𒃲 𒉒 𒌦 𒋧"        # cuneiform -> English
python cuneiform.py                          # interactive mode
```

In interactive mode, switch modes with `:mode logograms`, `:mode translit` or `:mode hybrid`; an empty line quits.
On Windows the script switches stdin/stdout to UTF-8 by itself.

As a library:

```python
from cuneiform import translate

print(translate("The great king gave bread to the people", mode="hybrid"))
print(translate("𒈗 𒃲 𒉒 𒌦 𒋧"))            # -> great king give bread people
```

## Modes

| Mode | What it does |
|---|---|
| `logograms` | Only Sumerian logograms from the dictionary. Words that are not in the dictionary are kept as `⟨word⟩`, so nothing is lost and the reverse translation restores them. |
| `translit` | Pure transliteration: the English text is spelled phonetically with syllabic signs. Word order and function words are kept. |
| `hybrid` (default) | Logograms where the word is in the dictionary, syllabic spelling for the rest. Syllabic words start with the marker sign U+12470 so they can be told apart from logograms when translating back. |

Examples (`--explain` prints a word-by-word breakdown):

```text
$ python cuneiform.py --mode logograms "The great king gave bread to the people"
𒈗 𒃲 𒉒 𒌦 𒋧

$ python cuneiform.py --mode hybrid --explain "King David saw 3 cities"
𒈗 𒑰𒁕𒁉𒁲 𒁹𒁹𒁹 𒌷𒌷 𒅆

King         lugal            𒈗          logogram
David        da-bi-di         𒑰𒁕𒁉𒁲       syllabic spelling (not in dictionary)
saw          igi              𒅆          logogram
3            —                𒁹𒁹𒁹        number
cities       uru×2            𒌷𒌷         logogram

$ python cuneiform.py "𒈗 𒃲 𒉒 𒌦 𒋧"
great king give bread people
```

## How it works

- **Logograms.** A dictionary maps English words (with synonyms, plurals, verb forms and irregular forms) to Sumerian signs. Sign names are resolved through Python's `unicodedata`, so the signs are always real Unicode characters.
- **Sumerian-style grammar** (logogram and hybrid modes): function words (`the`, `is`, `of`, …) are dropped, the verb goes to the end of the clause (SOV), adjectives follow the noun, `king's palace` becomes `palace king`, a negation stays next to its verb, and the plural is written by repeating the sign (𒈗𒈗 = kings).
- **Numbers** 1–59 are written with the sign for 1 and the sign for 10, repeated.
- **Syllabic spelling.** English is converted to a rough phoneme string, then split into syllables. The syllable table (V, CV, VC and CVC signs, 153 in total) is generated from Unicode sign names. When a syllable has no sign of its own it is combined from several signs (`bank` → `ba-an-ak`). Following Hurrian-style spelling, voiced and voiceless consonants are interchangeable (b/p, d/t, g/k), `e` and `i` are interchangeable, and `o` is written as `u`.
- **Reverse translation.** Signs are mapped back to English glosses, reduplicated signs become plurals, and the word order is turned back from SOV to SVO. Syllabic words are shown as `‹phonetic›` (or plain text in `translit` mode).

## Project layout

```text
cuneiform.py   translator and command-line interface
_dict.py       dictionary data (see below)
README.md      this file
```

`_dict.py` provide:

- `LEXICON` – a multi-line string, one entry per line: `english words | reading | SIGN NAMES | pos`
  - several English synonyms are separated by commas;
  - sign names are Unicode names without the `CUNEIFORM SIGN ` prefix; compound words join signs with `+`;
  - `pos` is one of `n`, `adj`, `v`, `pron`, `neg`.

  ```text
  king,ruler,monarch | lugal | LUGAL | n
  palace | e2-gal | E2+GAL | n
  great,big,large | gal | GAL | adj
  give | sum | SUM | v
  ```

- `NUM_WORDS` – number words to values, e.g. `{"one": 1, "ten": 10, "twenty": 20}`
- `STOPWORDS` – a set of function words that are skipped in logogram and hybrid modes
- `IRREGULAR` – irregular forms to base forms, e.g. `{"gave": "give", "children": "child"}`
- `IRREG_PLURAL` – base forms to irregular plurals, e.g. `{"child": "children"}`

To extend the dictionary, add lines to `LEXICON`. Entries whose sign name does not exist in Unicode are skipped and listed in `cuneiform.MISSING`, so a quick check after editing is `python -c "import cuneiform; print(cuneiform.MISSING)"`.

## Limitations

- This is a dictionary-based translator, not a full machine-translation system: there is no Sumerian morphology (cases, verb prefixes), no tense, and only a few pronouns.
- Possession cannot be recovered when translating back (`palace king` is not turned into `king's palace`).
- Syllabic spelling is lossy in both directions (voicing, `e`/`i`, silent letters), so a round trip in `translit` or `hybrid` mode gives an approximate phonetic form of unknown words, not the original spelling.
- Ambiguous signs (e.g. 𒀭 = *god* / *sky*, 𒅗 = *mouth* / *say*) are resolved heuristically by position in the clause.
- Some Sumerian logograms have no Unicode name that this project could verify, so those words are not in the dictionary.
