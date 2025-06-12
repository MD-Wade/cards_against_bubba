#!/usr/bin/env python3
import os
import json
from pathlib import Path
import re
import Levenshtein

def normalize(text):
    # Lowercase, collapse whitespace, remove non-letters except blanks and basic punctuation
    return re.sub(r'\s+', ' ', text.strip().lower())

def collect_prompts(input_dir):
    prompts = []
    for dirpath, _, files in os.walk(input_dir):
        for fn in files:
            if fn.lower().endswith('.json'):
                src = Path(dirpath)/fn
                with open(src, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except Exception as e:
                        continue
                if isinstance(data, list):
                    cards = data
                elif isinstance(data, dict):
                    cards = data.get("cards", [data])
                else:
                    continue
                for idx, card in enumerate(cards):
                    if card.get("type") == "prompt":
                        text = card.get("text", "")
                        prompts.append((normalize(text), text, src, idx))
    return prompts

def fuzzy_duplicates(prompts, threshold=0.05):
    # Compare each prompt to every other (naive N^2 for simplicity)
    results = []
    n = len(prompts)
    for i in range(n):
        norm_i, raw_i, file_i, idx_i = prompts[i]
        for j in range(i+1, n):
            norm_j, raw_j, file_j, idx_j = prompts[j]
            # Minimum length to compare as percent
            min_len = min(len(norm_i), len(norm_j))
            if min_len < 10:  # too short, skip
                continue
            dist = Levenshtein.distance(norm_i, norm_j)
            if min_len == 0:
                continue
            rel_dist = dist / min_len
            if rel_dist <= threshold:
                results.append((
                    f"SIMILAR ({rel_dist*100:.1f}% diff):\n"
                    f"  {file_i}: [{idx_i}] {raw_i}\n"
                    f"  {file_j}: [{idx_j}] {raw_j}\n"
                ))
    return results

def main():
    input_dir = 'data_raw'
    prompts = collect_prompts(input_dir)
    results = fuzzy_duplicates(prompts, threshold=0.05)
    if results:
        print("Fuzzy duplicate prompts found:\n")
        for res in results:
            print(res)
    else:
        print("No fuzzy duplicates found.")

if __name__ == '__main__':
    main()
