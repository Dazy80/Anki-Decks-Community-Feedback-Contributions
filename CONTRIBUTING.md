# Contributing

Thank you for helping to improve the decks! You need a free GitHub account. There are two ways:

1. **Report a mistake.** [Open the form](https://github.com/Dazy80/Anki-Decks-Community-Feedback-Contributions/issues/new/choose) and give the number after **Freq.n:** on the card, the German word and what is wrong. One report can list many notes.
2. **Correct it yourself.** All notes of the deck "20.000 häufige Wörter" are in CSV files in [`decks/20000-german-words/notes`](decks/20000-german-words/notes) – one row per note. Edit them and send a pull request. It is checked automatically and then reviewed.

## Correct a note on GitHub – no software needed

1. **Find the file.** Each file holds 500 notes and is named after their numbers: note 1234 is in `01001-01500.csv`.
2. **Open it and click the pencil** (Edit this file). The first time, GitHub asks you to fork the repository – that is your own copy, click "Fork this repository".
3. **Find the row.** Every row starts with the number of the note. Search in the editor with Ctrl+F (⌘F on a Mac), e.g. for `1234,`.
4. **Change only the text you want to correct.** Keep the commas between the columns. Text that contains a comma or a quote mark stays inside `"…"`, and a quote mark inside the text is written twice: `""`.
5. **Click "Commit changes…"**, say in a few words what you corrected, click "Propose changes" and then "Create pull request".

That's all. The automatic check now runs on your pull request: a green ✓ means the format is fine. A red ✗? Click "Details" – it says what to fix and where. You can change the file again in the same pull request: tab "Files changed" → "⋯" → "Edit file".

The check also lists every field you changed (in "Details" → "Summary"), so you can see that only your corrections changed.

## Rules

- **One row = one note.** Never add, remove or move rows, and never change `Frequency_number` or `GUID` – they identify the note in Anki.
- **What the columns mean** and the codes for `Article` and `Type`: see [decks/20000-german-words/README.md](decks/20000-german-words/README.md).
- **German example sentences (`Ex_german`):** please don't change them. Each sentence has its own audio, a cloze card and hints. If a sentence is wrong, report it with the form.
- **German word (`Word`):** only fix the capital letter or an obvious typo.
- **Translations** should be natural and match the German sentence. Spanish is European Spanish (tú, usted, vosotros), as in the rest of the deck.
- **Keep HTML** such as `<br>` where it is.
- **One kind of correction per pull request** (e.g. "Spanish translations 1–500") makes the review easy. Many notes in one pull request are welcome.

## Many changes? Use a spreadsheet – carefully

- Use **LibreOffice Calc** or **Google Sheets**, not Excel – Excel changes quotes and special characters and can turn values starting with `-`, `+` or `=` into formulas. Some values in the column `GUID` start with these characters.
- **LibreOffice:** in the import dialog choose character set "Unicode (UTF-8)" and separator "Comma", then click the top-left corner of the preview to select all columns and set the column type to "Text". Save as CSV: keep the format, character set UTF-8, field delimiter `,`, string delimiter `"`.
- **Google Sheets:** File → Import → Upload, and untick "Convert text to numbers, dates, and formulas". Afterwards File → Download → Comma-separated values (.csv).
- Upload the file to your fork with exactly the same name (Add file → Upload files) and create a pull request. The check shows which fields changed.

## What happens next

The maintainer reviews your pull request and merges it, or asks a question in it. Accepted corrections go into the next version of the deck on AnkiWeb.

By sending a report or a pull request, you agree that your corrections may be included in the decks and shared publicly (on AnkiWeb, on MEGA and in this repository).
