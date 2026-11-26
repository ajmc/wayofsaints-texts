# The Raccolta (1910): 73 prayers, transcribed from the scan

73 of the best-known prayers of *The Raccolta, or Collection of Indulgenced Prayers and Good Works*, in the
authorized English translation by Ambrose St John (London: Burns & Oates, 1910). Each one is transcribed from the
printed page.

## Source

- **Edition:** *The Raccolta*, authorized English translation, Burns & Oates, London, 1910.
- **Scan:** the University of St. Michael's College (Toronto) copy on the Internet Archive:
  https://archive.org/details/theraccoltaorcol00unknuoft. As far as we know, it is the only scan of this edition.
- **Wikisource** has the same scan set up for proofreading
  ([Index:Theraccoltaorcol00unknuoft.djvu](https://en.wikisource.org/wiki/Index:Theraccoltaorcol00unknuoft.djvu)).
  In November 2026, 6 of its 458 pages were proofread.

## Files

| File | What |
|---|---|
| `prayers.json` | The 73 prayers: `number` (the entry number in the book), `section`, `title` and `text` (a list of paragraphs) |
| `prayers.txt` | The same, as plain text |
| `ocr-draft/raccolta-ocr.json` | **Unchecked** draft of all 446 entries, made automatically from archive.org's OCR of the scan |
| `ocr-draft/build.py` | The script that made the draft. It needs the [Way of Saints](https://wayofsaints.com) code to run, and is kept here as a record of the method |

## Method

**The 73 prayers** were transcribed from the scanned page images, then compared with archive.org's OCR of the
same scan.

**The OCR draft** comes from archive.org's OCR, which records the position of each word. The script uses those
positions to separate the Latin and English that the book prints side by side. It then splits the text into
entries and repairs common OCR errors.

## Conventions

- A line written `_like this_` is a rubric (an instruction), printed in italics in the book.
- ℣ and ℟ are the book's versicle and response signs; ✠ is its sign of the cross.
- The spelling, capitals and punctuation are the book's.

## Known limits

- **Proofreading:** the 73 prayers have not yet been proofread a second time, against the scan, by a person.
- **Indulgences:** they are left out of the 73 prayers. The book gives one after each prayer, but the Church revised
  them in 1968 (*Enchiridion of Indulgences*).
- **Page numbers:** none are recorded for the 73 prayers yet.
- **The OCR draft has many errors.** For example, entry 1 reads "LorpGopof Hosts" for "Lord God of Hosts", and some
  entries have lost their headings or run into the next. It is raw material for proofreading, not a text to quote.

## Licence

The book is in the public domain. These transcriptions are released under CC0 1.0 (see `LICENSE` at the top of
the repository): use them freely. A credit and a link to https://wayofsaints.com are welcome.
