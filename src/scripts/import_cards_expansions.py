#!/usr/bin/env python3
import csv
import json
import re
import os

# Always‐true regions for this file
REGIONS = ['US', 'UK', 'CA', 'AU', 'INTL']

def parse_vertical_packs(csv_path, output_dir):
    # 1) Read every row into memory
    with open(csv_path, newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))

    i = 0
    while i < len(rows):
        row = rows[i]
        # 2) Detect the start of a new pack block: a row like ["Set", "<Pack Name>", ...]
        if len(row) > 1 and row[0].strip() == 'Set' and row[1].strip():
            pack_name = row[1].strip()
            slug = re.sub(r'[^a-z0-9_]', '', pack_name.lower().replace(' ', '_'))

            cards = []
            i += 1
            # 3) Skip any metadata until we hit the first card
            while i < len(rows) and (not rows[i] or rows[i][0].strip() not in ('Prompt', 'Response')):
                i += 1

            # 4) Collect all cards until the next "Set" row or end‐of‐file
            while i < len(rows):
                r = rows[i]
                # if we see a new pack header, break out
                if len(r) > 1 and r[0].strip() == 'Set' and r[1].strip():
                    break

                typ = r[0].strip() if r else ''
                if typ in ('Prompt', 'Response'):
                    text    = r[1].strip() if len(r) > 1 else ''
                    special = r[2].strip() if len(r) > 2 else ''

                    card = {
                        "text": text,
                        "type": typ.lower(),
                        # every region is true for this file
                        "regions": {reg.lower(): True for reg in REGIONS}
                    }
                    if typ == 'Prompt':
                        m = re.search(r'PICK\s*(\d+)', special, re.IGNORECASE)
                        card["pick"] = int(m.group(1)) if m else 1

                    cards.append(card)

                i += 1

            # 5) Write out this pack’s JSON
            os.makedirs(output_dir, exist_ok=True)
            out_path = os.path.join(output_dir, f"{slug}.json")
            with open(out_path, 'w', encoding='utf-8') as jf:
                json.dump(cards, jf, indent=2, ensure_ascii=False)
            print(f"Wrote {len(cards)} cards to {out_path}")

        else:
            i += 1


if __name__ == '__main__':
    parse_vertical_packs(
        csv_path   = 'data/pack_extra.csv',  # or wherever your file lives
        output_dir = 'data'                  # JSONs will land here
    )
