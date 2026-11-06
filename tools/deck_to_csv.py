#!/usr/bin/env python3
"""Write the notes of the deck "20.000 häufige Wörter" as CSV files.

Maintainer tool – contributors don't need it.

    pip install anki
    python tools/deck_to_csv.py path/to/deck.apkg

Reads all notes of the note type "10000_Wörter" from an Anki package (.apkg)
or a collection file (.anki2) and writes decks/20000-german-words/notes/*.csv:
one row per note, 500 notes per file (by Frequency_number), UTF-8, commas.
Existing CSV files in that folder are replaced.
"""
import csv
import os
import shutil
import sys
import tempfile

NOTETYPE = '10000_Wörter'
FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'decks', '20000-german-words', 'notes')
COLUMNS = ['Frequency_number', 'Word', 'Article', 'Type', 'IPA', 'Word_english', 'Word_spanish',
           'Ex_german', 'Ex_english', 'Ex_spanish', 'Definition', 'ES', 'GUID']
PER_FILE = 500


def read_notes(path):
    from anki.collection import Collection, ImportAnkiPackageOptions, ImportAnkiPackageRequest

    tmp = tempfile.mkdtemp()
    try:
        if path.endswith('.anki2'):
            col_path = os.path.join(tmp, 'collection.anki2')
            shutil.copy(path, col_path)
            col = Collection(col_path)
        else:
            col = Collection(os.path.join(tmp, 'collection.anki2'))
            col.import_anki_package(ImportAnkiPackageRequest(
                package_path=os.path.abspath(path), options=ImportAnkiPackageOptions(with_scheduling=False)))
        notes = []
        for nid in col.find_notes(f'"note:{NOTETYPE}"'):
            note = col.get_note(nid)
            row = {name: note[name] for name in COLUMNS if name != 'GUID'}
            row['GUID'] = note.guid
            notes.append(row)
        col.close()
        return notes
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def write_csv(notes, folder=FOLDER):
    notes = sorted(notes, key=lambda r: int(r['Frequency_number']))
    os.makedirs(folder, exist_ok=True)
    for name in os.listdir(folder):
        if name.endswith('.csv'):
            os.remove(os.path.join(folder, name))
    blocks = {}
    for row in notes:
        start = (int(row['Frequency_number']) - 1) // PER_FILE * PER_FILE + 1
        blocks.setdefault(start, []).append(row)
    for start, rows in sorted(blocks.items()):
        name = f'{start:05d}-{start + PER_FILE - 1:05d}.csv'
        with open(os.path.join(folder, name), 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow(COLUMNS)
            for row in rows:
                writer.writerow([row[c] for c in COLUMNS])
    return len(blocks)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    notes = read_notes(sys.argv[1])
    if not notes:
        sys.exit(f'No notes of the note type "{NOTETYPE}" found.')
    files = write_csv(notes)
    print(f'{len(notes)} notes written to {files} files in {os.path.normpath(FOLDER)}')


if __name__ == '__main__':
    main()
