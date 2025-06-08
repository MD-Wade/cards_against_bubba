import csv, json, re

REGIONS = ['US', 'UK', 'CA', 'AU', 'INTL']

def parse_csv_to_json(csv_path, json_path):
    # 1. Read all lines
    with open(csv_path, encoding='utf-8') as f:
        lines = f.readlines()

    # 2. Locate header and grouping lines
    header_i   = next(i for i, line in enumerate(lines) if line.startswith('Set,'))
    group_line = lines[header_i - 1]
    data_start = header_i + 2

    # 3. Count total columns from grouping line
    raw_groups = [cell.strip().strip('"').upper() for cell in group_line.strip().split(',')]
    total_cols = len(raw_groups)

    # 4. Map region → list of indices
    region_indices = {
        region: [i for i, g in enumerate(raw_groups) if g == region]
        for region in REGIONS
    }

    cards = []
    for line in lines[data_start:]:
        row = next(csv.reader([line.strip()])) if line.strip() else []
        if len(row) < total_cols:
            row += [''] * (total_cols - len(row))

        if not row or row[0] not in ('Prompt', 'Response'):
            continue

        ctype   = row[0].lower()
        text    = row[1].strip()
        special = row[2].strip()

        card = {"text": text, "type": ctype}

        if ctype == 'prompt':
            # look for explicit PICK N
            m = re.search(r'PICK\s*(\d+)', special, re.IGNORECASE)
            card["pick"] = int(m.group(1)) if m else 1

        # regions object
        regions = {}
        for region, idxs in region_indices.items():
            regions[region.lower()] = any(row[i].strip() for i in idxs)
        card["regions"] = regions

        cards.append(card)

    # Sanity-check print
    print("First 20 parsed cards:")
    for c in cards[:20]:
        print(c)

    # Write JSON
    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(cards, jf, indent=2, ensure_ascii=False)
    print(f"\nConverted {len(cards)} cards → {json_path}")

if __name__ == '__main__':
    parse_csv_to_json(
        csv_path = 'data/pack_main.csv',
        json_path = 'data/pack_main.json'
    )
