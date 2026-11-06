#!/usr/bin/env python3
"""Check the CSV files of the deck "20,000 Frequent German Words".

Runs automatically for every pull request (.github/workflows/check-csv.yml).
You can also run it yourself – Python 3.8 or newer, nothing to install:

    python tools/check_csv.py               check all files
    python tools/check_csv.py --base main   also list what changed compared with a branch or commit

Errors make the check fail. Warnings are hints for the person who reviews the change.
"""
import argparse
import csv
import io
import itertools
import os
import re
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FOLDER = 'decks/20000-german-words/notes'
COLUMNS = ['Frequency_number', 'Word', 'Article', 'Type', 'IPA', 'Word_english', 'Word_spanish',
           'Ex_german', 'Ex_english', 'Ex_spanish', 'Definition', 'ES', 'GUID']
PER_FILE = 500
LOCKED = ('Frequency_number', 'GUID')
REQUIRED = [c for c in COLUMNS if c != 'Article']
FILE_NAME = re.compile(r'(\d{5})-(\d{5})\.csv')

# Type: one or more parts separated by "; ", e.g. "adj; adv", "M (pl)", "F (pl, fw)".
GENDER = re.compile(r'[MFN](/[MFN])*|nnpl')
WORD_CLASSES = {'vb', 'vbr', 'av', 'vb2', 'adj', 'adv', 'prn', 'phr', 'abbr', 'frag',
                'prp', 'con', 'nu', 'i', 'art', 'cntr', 'prt', 'pfx', 'sfx', 'name'}
FORMS = ('pl', 'gen', 'dat', 'akk', 'dat pl', 'gen pl')
PART = re.compile(r'(\S+?)(?: \(([^()]*)\))?')
CAPITAL_OK = {'name', 'abbr', 'frag', 'phr'}   # word classes that may start with a capital letter

GENDER_ARTICLE = {'M': 'der', 'F': 'die', 'N': 'das'}


def allowed_articles(code, form):
    """Articles that fit a noun code (M, F, N, M/F, N/M …, nnpl) and an optional form."""
    if code == 'nnpl':
        return {'': {'die'}, 'pl': {'die'}, 'dat pl': {'den'}, 'gen pl': {'der'}}.get(form, set())
    letters = code.split('/')
    if form in ('pl', 'dat pl', 'gen pl', 'akk'):
        return {'pl': {'die'}, 'dat pl': {'den'}, 'gen pl': {'der'}, 'akk': {'den'}}[form]
    if form in ('gen', 'dat'):
        result = set()
        if 'M' in letters or 'N' in letters:
            result.add('des' if form == 'gen' else 'dem')
        if 'F' in letters:
            result.add('der')
        return result
    singles = [GENDER_ARTICLE[x] for x in letters]
    result = set(singles)
    for n in range(2, len(singles) + 1):
        result.update('/'.join(p) for p in itertools.permutations(dict.fromkeys(singles), n))
    if 'M' in letters and 'F' in letters:
        result.add('')   # strong form without article: "Verwandter", "Angestellter"
    return result


def check_type_and_article(type_, article):
    """Return a list of problems with Type and Article (empty list = fine)."""
    problems = []
    parts = type_.split('; ')
    first_code, first_form = None, ''
    for i, part in enumerate(parts):
        m = PART.fullmatch(part)
        if not m:
            problems.append(f'Type: "{part}" is not a valid part (separate several word types with "; ")')
            continue
        code, extra = m.group(1), m.group(2)
        is_noun = bool(GENDER.fullmatch(code))
        if ';' in code or ',' in code:
            problems.append(f'Type: "{part}" is not a valid part (separate several word types with "; " – '
                            'semicolon and space)')
        elif not is_noun and code not in WORD_CLASSES:
            problems.append(f'Type: unknown code "{code}" (see the list of codes in decks/20000-german-words/README.md)')
        form = ''
        if extra is not None:
            if i > 0:
                problems.append(f'Type: "({extra})" is only allowed after the first word type')
            tokens = extra.split(', ')
            fw = tokens[-1] == 'fw'
            if fw:
                tokens = tokens[:-1]
                if code == 'name':
                    problems.append('Type: names never get "(fw)"')
            if len(tokens) > 1 or (tokens and tokens[0] not in FORMS):
                problems.append(f'Type: "({extra})" – allowed are pl, gen, dat, akk, dat pl, gen pl and/or fw')
            elif tokens:
                form = tokens[0]
                if not is_noun:
                    problems.append(f'Type: a form like "({form})" only goes with a noun code (M, F, N, nnpl …)')
        if i == 0:
            first_code, first_form = code, form
    if first_code is None or problems:
        return problems
    if GENDER.fullmatch(first_code):
        ok = allowed_articles(first_code, first_form)
        if article not in ok:
            want = ' or '.join(f'"{a}"' if a else 'empty' for a in sorted(ok)) or 'nothing'
            form_text = f' ({first_form})' if first_form else ''
            problems.append(f'Article "{article}" does not fit Type "{first_code}{form_text}" – expected {want}')
    elif article:
        problems.append(f'Article "{article}" – only nouns have an article (Type starts with "{first_code}")')
    return problems


class Report:
    def __init__(self):
        self.messages = []   # (level, path, line, text)
        self.changes = []    # (path, line, number, word, column, old, new)
        self.files = 0
        self.notes = 0
        self.compared = None       # the base, if the files were compared with it
        self.first_upload = False  # the base has no CSV files yet

    def error(self, path, line, text):
        self.messages.append(('error', path, line, text))

    def warning(self, path, line, text):
        self.messages.append(('warning', path, line, text))

    def count(self, level):
        return sum(1 for m in self.messages if m[0] == level)


def parse(text, path, report, quiet=False):
    """Return the header and a list of (line number, row) – or (None, None) if the file can't be read."""
    if not text.strip():
        report.error(path, 1, 'The file is empty.')
        return None, None
    if text.startswith('﻿'):
        text = text[1:]
        if not quiet:
            report.warning(path, 1, 'The file starts with a BOM – please save it as UTF-8 without BOM.')
    if '\r\n' in text and not quiet:
        report.warning(path, 1, 'Windows line endings (CRLF) – every line will show as changed. '
                                'Please save with LF line endings if you can.')
    reader = csv.reader(io.StringIO(text, newline=''), strict=True)
    rows, line = [], 1
    try:
        header = next(reader, None)
        line = reader.line_num + 1
        for row in reader:
            rows.append((line, row))
            line = reader.line_num + 1
    except csv.Error as e:
        report.error(path, line, f'The file cannot be read as CSV here ({e}). Usually a quote mark " is missing '
                                 'or too many – text with commas or quotes must stay inside "…", '
                                 'and a " inside the text is written as "".')
        return None, None
    return header, rows


def read_rows(text, path, report, quiet=False):
    """Parse and check the structure of one file. Returns {GUID: (line, dict)} in file order, or None."""
    header, rows = parse(text, path, report, quiet)
    if header is None:
        return None
    if header != COLUMNS:
        report.error(path, 1, 'The first line must be exactly: ' + ','.join(COLUMNS))
        return None
    m = FILE_NAME.fullmatch(os.path.basename(path))
    first, last = (int(m.group(1)), int(m.group(2))) if m else (None, None)
    result, previous = {}, 0
    for line, row in rows:
        if len(row) != len(COLUMNS):
            report.error(path, line, f'{len(row)} columns instead of {len(COLUMNS)} – a comma or a quote mark '
                                     'is probably missing or too many in this line.')
            continue
        values = dict(zip(COLUMNS, row))
        number = values['Frequency_number']
        if not number.isdigit():
            report.error(path, line, f'Frequency_number "{number}" is not a number.')
            continue
        if first is not None and not first <= int(number) <= last:
            report.error(path, line, f'Frequency_number {number} does not belong in this file ({first}–{last}).')
        if int(number) <= previous:
            report.error(path, line, f'Frequency_number {number} is out of order or appears twice.')
        previous = int(number)
        if values['GUID'] in result:
            report.error(path, line, f'GUID {values["GUID"]} appears twice.')
        result[values['GUID']] = (line, values)
    return result


def check_values(path, line, values, report, level):
    for column in REQUIRED:
        if not values[column].strip():
            level(path, line, f'{column} must not be empty (note {values["Frequency_number"]}).')
    for problem in check_type_and_article(values['Type'], values['Article']):
        level(path, line, f'{problem} (note {values["Frequency_number"]} "{values["Word"]}")')


def capital_hint(values):
    word = values['Word']
    m = PART.fullmatch(values['Type'].split('; ')[0])
    code = m.group(1) if m else ''
    if not word[:1].isalpha():
        return None
    if word[0].isupper() and code in WORD_CLASSES and code not in CAPITAL_OK:
        return f'"{word}" starts with a capital letter, but Type is "{code}" – only nouns and names are capitalized.'
    if word[0].islower() and GENDER.fullmatch(code):
        return f'"{word}" is a noun (Type "{code}") – nouns start with a capital letter.'
    return None


def compare(path, old, new, report):
    """Compare two versions of a file (dicts from read_rows) and record the changes."""
    old_keys = [(v['Frequency_number'], g) for g, (_, v) in old.items()]
    new_keys = [(v['Frequency_number'], g) for g, (_, v) in new.items()]
    if old_keys != new_keys:
        lines = [line for line, _ in new.values()]
        for i, (a, b) in enumerate(itertools.zip_longest(old_keys, new_keys)):
            if a != b:
                line = lines[i] if i < len(lines) else (lines[-1] if lines else 1)
                report.error(path, line, 'Rows were added, removed or moved, or Frequency_number/GUID changed '
                                         f'(first difference: before {a}, now {b}). Please only change text in the '
                                         'existing rows and never Frequency_number or GUID.')
                break
        return
    for guid, (line, values) in new.items():
        before = old[guid][1]
        changed = [c for c in COLUMNS if values[c] != before[c]]
        if not changed:
            continue
        for column in changed:
            report.changes.append((path, line, values['Frequency_number'], values['Word'], column,
                                   before[column], values[column]))
        check_values(path, line, values, report, report.error)
        number, word = values['Frequency_number'], values['Word']
        if 'Ex_german' in changed:
            report.warning(path, line, f'Note {number} "{word}": the German sentence changed. Its audio, the '
                                       'cloze and the hints of the sentence do not change with it – the maintainer '
                                       'decides whether they have to be redone.')
        if 'Word' in changed and values['Word'].lower() != before['Word'].lower():
            report.warning(path, line, f'Note {number}: the German word changed ("{before["Word"]}" → "{word}"), '
                                       'not only its capitalization. The audio of the word stays the same.')
        if 'Word' in changed or 'Type' in changed:
            hint = capital_hint(values)
            if hint:
                report.warning(path, line, f'Note {number}: {hint}')
        for column in ('Definition', 'ES'):
            if column in changed and not values[column].lstrip().startswith('【'):
                report.warning(path, line, f'Note {number}: {column} should start like before, '
                                           'with 【word】★★★★★<br>.')
        for column in changed:
            value = values[column]
            if (value != value.strip() or '  ' in value) and not (before[column] != before[column].strip()
                                                                   or '  ' in before[column]):
                report.warning(path, line, f'Note {number}: {column} has a space at the start or end, '
                                           'or two spaces in a row.')


def git(*args):
    return subprocess.run(['git', '-C', ROOT, *args], capture_output=True, check=True).stdout


def run(base=None):
    report = Report()
    seen = {}   # GUID -> file, for GUIDs that appear in two files
    folder = os.path.join(ROOT, FOLDER)
    names = sorted(n for n in os.listdir(folder) if n.endswith('.csv')) if os.path.isdir(folder) else []
    base_names = None
    if base:
        try:
            git('rev-parse', '--verify', '--quiet', base + '^{commit}')
        except subprocess.CalledProcessError:
            report.error(FOLDER, 1, f'Unknown branch or commit "{base}".')
            return report
        listing = git('ls-tree', '--name-only', base, FOLDER + '/').decode('utf-8').splitlines()
        base_names = sorted(os.path.basename(p) for p in listing if p.endswith('.csv'))
        if not base_names:
            report.first_upload = True   # nothing to compare with yet: check all rows
            base_names = None
        else:
            report.compared = base
        for name in sorted(set(base_names or []) - set(names)):
            report.error(f'{FOLDER}/{name}', 1, 'This file was deleted. Please keep all files.')
    for name in names:
        path = f'{FOLDER}/{name}'
        report.files += 1
        if not FILE_NAME.fullmatch(name):
            report.error(path, 1, 'Unexpected file name – the files are named like 00001-00500.csv.')
        with open(os.path.join(ROOT, path), 'rb') as f:
            data = f.read()
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError as e:
            line = data[:e.start].count(b'\n') + 1
            report.error(path, line, 'Not UTF-8 – please save the file as "UTF-8".')
            continue
        rows = read_rows(text, path, report)
        if rows is None:
            continue
        report.notes += len(rows)
        for guid, (line, _) in rows.items():
            if guid in seen:
                report.error(path, line, f'GUID {guid} also appears in {seen[guid]}.')
            seen[guid] = name
        if base_names is None:
            for guid, (line, values) in rows.items():
                check_values(path, line, values, report, report.error)
            continue
        if name not in base_names:
            report.error(path, 1, 'This file is new. Please only change the existing files.')
            continue
        old_report = Report()
        old = read_rows(git('show', f'{base}:{path}').decode('utf-8'), path, old_report, quiet=True)
        if old is None:
            for guid, (line, values) in rows.items():
                check_values(path, line, values, report, report.error)
            continue
        compare(path, old, rows, report)
    return report


def cell(text, limit=120):
    text = text.replace('\r', '').replace('\n', ' ⏎ ')
    if len(text) > limit:
        text = text[:limit] + '…'
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '\\|') or '∅'


def summary(report):
    errors, warnings = report.count('error'), report.count('warning')
    out = []
    if errors:
        out.append(f'## ❌ CSV check: {errors} error{"s" * (errors != 1)}')
    else:
        out.append('## ✅ CSV check passed')
    out.append(f'{report.files} files, {report.notes} notes checked.')
    if report.first_upload:
        out.append('First upload of the files – nothing to compare with yet, so all rows were checked.')
    elif report.compared:
        notes = len({(c[0], c[2]) for c in report.changes})
        out.append(f'Compared with `{report.compared[:12]}`: **{notes} notes, {len(report.changes)} fields changed.**')
    for level, title in (('error', 'Errors'), ('warning', 'Warnings')):
        items = [m for m in report.messages if m[0] == level]
        if items:
            out.append(f'\n### {title}\n')
            for _, path, line, text in items[:200]:
                out.append(f'- `{os.path.basename(path)}` line {line}: {cell(text, 400)}')
            if len(items) > 200:
                out.append(f'- … and {len(items) - 200} more')
    if report.changes:
        out.append('\n### Changes\n')
        out.append('| File | Line | No. | Word | Field | Before | After |')
        out.append('|---|---|---|---|---|---|---|')
        for path, line, number, word, column, old, new in report.changes[:300]:
            out.append(f'| {os.path.basename(path)} | {line} | {number} | {cell(word, 40)} | {column} '
                       f'| {cell(old)} | {cell(new)} |')
        if len(report.changes) > 300:
            out.append(f'\n… and {len(report.changes) - 300} more changed fields.')
    return '\n'.join(out) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--base', help='branch or commit to compare with (e.g. main)')
    args = parser.parse_args(argv)
    base = args.base if args.base and set(args.base) != {'0'} else None
    report = run(base)

    for level, path, line, text in report.messages:
        print(f'{level.upper()}: {path}:{line}: {text}')
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            safe = text.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
            print(f'::{level} file={path},line={line}::{safe}')
    for path, line, number, word, column, old, new in report.changes:
        print(f'CHANGED: {path}:{line}: {number} {word} – {column}: {old!r} → {new!r}')
    errors, warnings = report.count('error'), report.count('warning')
    if report.first_upload:
        print('First upload of the files – nothing to compare with yet, so all rows were checked.')
    print(f'{report.files} files, {report.notes} notes: {errors} errors, {warnings} warnings, '
          f'{len(report.changes)} changed fields.')
    summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(summary(report))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
