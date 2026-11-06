# 20.000 häufige Wörter – the notes as CSV

All 20,091 notes of the Anki deck **[20.000 häufige Wörter](https://ankiweb.net/shared/info/9239409)** (20,000 frequent German words, note type `10000_Wörter`), version 8.1 – one row per note, UTF-8, separated by commas.

- **Find a note:** the number after **Freq.n:** on the card. Each file holds 500 numbers: note 1234 is in [`notes/01001-01500.csv`](notes/01001-01500.csv).
- **Report a mistake:** [issue form](https://github.com/Dazy80/Anki-Decks-Community-Feedback-Contributions/issues/new/choose)
- **Correct it yourself:** [CONTRIBUTING.md](../../CONTRIBUTING.md)

Pictures, audio, the hints and the grammar info of the "Extra" card are not in these files – please report mistakes there with the issue form.

## Columns

| Column | What it is | Please note |
|---|---|---|
| `Frequency_number` | number of the note (Freq.n: on the card) | never change |
| `Word` | the German word | only fix the capital letter or a typo |
| `Article` | the article that goes with `Word` | only for nouns – see below |
| `Type` | word type (Type: on the card) | codes below |
| `IPA` | pronunciation | shown on the "Audio" and "Hören" cards |
| `Word_english`, `Word_spanish` | translations of the word | European Spanish |
| `Ex_german` | German example sentence | please don't change – it has its own audio; report it instead |
| `Ex_english`, `Ex_spanish` | translations of the sentence | European Spanish |
| `Definition` | meaning in English ("Bedeutung") | HTML; keep the start `【word】★★★★★<br>` |
| `ES` | meaning in Spanish, shown with the "ES" button | like `Definition` |
| `GUID` | Anki's ID of the note | never change |

## `Type`

One or more parts, separated by `; ` (semicolon and space), e.g. `adj; adv`. The first part is the one used in the example sentence.

**Nouns** get their gender:

| Code | Meaning | Example |
|---|---|---|
| `M`, `F`, `N` | masculine, feminine, neuter | der Tag, die Zeit, das Haus |
| `M/F` | adjective or participle used as a noun for people | der/die Reisende |
| `M/N`, `N/M` … | gender varies – the most common first | das/der Joghurt |
| `nnpl` | noun only in the plural | die Eltern |

**Other word types:**

| Code | Meaning | Code | Meaning |
|---|---|---|---|
| `vb` | verb, also any verb form | `prp` | preposition |
| `vbr` | reflexive verb | `con` | conjunction |
| `av` | auxiliary or modal verb | `nu` | number |
| `vb2` | from the original deck – please keep | `i` | interjection (na, hallo) |
| `adj` | adjective, also any adjective form | `art` | article |
| `adv` | adverb | `cntr` | pronominal adverb, contraction (dabei, darin, wofür) |
| `prn` | pronoun, determiner (jeder, seins) | `prt` | particle (bitte, okay) |
| `phr` | fixed phrase of several words | `pfx`, `sfx` | prefix, suffix |
| `abbr` | abbreviation without article (Hr, St) | `name` | proper name: person, place, company, title of a book or film |
| `frag` | not a word (fragment, encoding error) | | |

**In brackets, after the first part only:**

- the **form**, for nouns whose `Word` is not the base form: `(pl)` plural, `(gen)` genitive, `(dat)` dative, `(akk)` accusative, `(dat pl)`, `(gen pl)` – e.g. Bälle → `M (pl)`, Pferdes → `N (gen)`;
- `(fw)` for a **foreign word** not used in German (believe, adios) – established loan words (der Job, das Team) and names don't get it;
- both: `M (pl, fw)`.

## `Article`

Only when the first part of `Type` is a noun code, and it fits the form of `Word`:

| `Type` | `Article` |
|---|---|
| `M`, `F`, `N`, `nnpl` | der, die, das, die |
| `M/F` | der/die, der or die – empty for the form without article (Verwandter) |
| `M/N`, `N/M` … | both, in the same order (der/das), or one of them |
| `(pl)`, `(akk)`, `(dat pl)`, `(gen pl)` | die, den, den, der |
| `(gen)`, `(dat)` | des or dem for M and N, der for F |

Proper names that always have an article (die Schweiz, der Irak, die Alpen) are written like nouns. All other word types have no article.
