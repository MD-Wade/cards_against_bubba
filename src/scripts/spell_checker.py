#!/usr/bin/env python3
import os
import json
from pathlib import Path
import re
from spellchecker import SpellChecker

def extract_words(text):
    # Remove underscores and non-letters, then split
    return [w for w in re.findall(r"\b[a-zA-Z']+\b", text) if not w.isupper()]

def check_json_file(path, spell):
    errors = []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            errors.append(f"[PARSE ERROR] {path}: {e}")
            return errors

    if isinstance(data, list):
        cards = data
    elif isinstance(data, dict):
        cards = data.get("cards", [data])
    else:
        errors.append(f"[FORMAT ERROR] {path}: Not a list or dict")
        return errors

    for idx, card in enumerate(cards):
        if card.get("type") != "prompt":
            continue
        text = card.get("text", "")
        words = extract_words(text)
        misspelled = spell.unknown(words)
        if misspelled:
            errors.append(f"{path}: [{idx}] {text}\n    Misspelled: {', '.join(sorted(misspelled))}")
    return errors

def main():
    input_dir = 'data_raw'
    spell = SpellChecker()
    # Optionally add words to whitelist:
    # spell.word_frequency.load_words(['CAH', 'Jr.', 'AI', ...])

    total = 0
    bad = 0

    for dirpath, _, files in os.walk(input_dir):
        for fn in files:
            if fn.lower().endswith('.json'):
                src = Path(dirpath)/fn
                errors = check_json_file(src, spell)
                total += 1
                if errors:
                    bad += 1
                    for err in errors:
                        print(err)
    print(f"\nChecked {total} JSON files. Found {bad} files with issues.")

if __name__ == '__main__':
    main()
