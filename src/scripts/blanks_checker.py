#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path
import re

def count_blanks(text):
    # Matches ____, ___, or similar (at least two underscores in a row)
    return len(re.findall(r'_{2,}', text))

def check_json_file(path):
    errors = []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            errors.append(f"[PARSE ERROR] {path}: {e}")
            return errors

    # If the file is a list of cards
    if isinstance(data, list):
        cards = data
    # If the file is a dict with a "cards" key or similar
    elif isinstance(data, dict):
        # Try to guess where the prompts are
        if "cards" in data:
            cards = data["cards"]
        else:
            cards = [data]
    else:
        errors.append(f"[FORMAT ERROR] {path}: Not a list or dict")
        return errors

    for idx, card in enumerate(cards):
        if card.get("type") != "prompt":
            continue
        text = card.get("text", "")
        pick = card.get("pick", 1)
        blanks = count_blanks(text)

        if blanks == pick:
            continue
        if pick == 1 and blanks == 0:
            if text.strip().endswith('?'):
                continue
        errors.append(f"{path}: [{idx}] pick={pick} blanks={blanks} | {text}")


        if blanks != pick:
            errors.append(f"{path}: [{idx}] pick={pick} blanks={blanks} | {text}")

    return errors

def main():
    input_dir = 'data_raw'

    total = 0
    bad = 0

    for dirpath, _, files in os.walk(input_dir):
        for fn in files:
            if fn.lower().endswith('.json'):
                src = Path(dirpath)/fn
                errors = check_json_file(src)
                total += 1
                if errors:
                    bad += 1
                    for err in errors:
                        print(err)
    print(f"\nChecked {total} JSON files. Found {bad} files with issues.")

if __name__ == '__main__':
    main()
