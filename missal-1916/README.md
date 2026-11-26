# The Mass Every Day of the Year (1916): the Roman Missal in English

The English of the Roman Missal as printed in *The Mass Every Day of the Year* (1916): every Introit, Collect, Gradual (with its Tract, Alleluia or Sequence), Offertory, Secret, Communion and Postcommunion printed in full, the Ordinary of the Mass, and the Prefaces.

## Source

- **Edition:** *The Mass Every Day of the Year: The Roman Missal* (New York: P. J. Kenedy & Sons, 1916).
- **Scans** on the Internet Archive:
  - https://archive.org/details/TheMassEveryDayOfTheYear
  - https://archive.org/details/bwb_T3-CBT-174

## Files

| File | What |
|---|---|
| `missal.json` | `parts`: the propers in the book's order, each a `kind` (introit, collect, gradual…) and its `text`; `ordinary`; `prefaces` |
| `missal.txt` | The same, as plain text |

## Method

Each page of both scans was read afresh with Apple's Vision text recognition, which reads these pages better than the scans' own OCR. The OCR of each scan was compared word by word, and where the scans disagreed the reading of the majority (or, for two scans, the one that is a dictionary word) was kept. Running heads, page numbers and broken lines were then removed, and common OCR confusions of the typeface repaired.

## Known limits

- **OCR errors remain.** About 0.43% of lower-case words are not in a spelling dictionary. That figure is an upper bound: it also counts British spellings, Latin and proper names. The text has been corrected by machine, not proofread by a person; corrections are welcome.
- The propers are in the book's order but not labelled with the Mass they belong to.
- The book's short explanations ("Meaning entrance or beginning…") are kept where it prints them.

About 133,189 words.

## Licence

The book is in the public domain. This text is released under CC0 1.0 (see `LICENSE` at the top of the repository): use it freely. A credit and a link to https://wayofsaints.com are welcome.
