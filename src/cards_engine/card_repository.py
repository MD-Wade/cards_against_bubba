# card_repository.py

import os
import json
from glob import glob
from typing import List, Optional, Dict
from collections import defaultdict
from pathlib import Path

import zstandard as zstd

from .card import Card

class CardRepository:
    def __init__(self, path_pattern: Optional[str] = None):
        self._path_pattern = path_pattern or self._default_path_pattern()
        self._cards: List[Card] = self._load_all(self._path_pattern)

    def _default_path_pattern(self) -> str:
        here = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(here, "..", ".."))
        data_dir = os.path.join(project_root, "data")
        # include both .json and .json.zst
        return os.path.join(data_dir, "*.json*")

    def _load_all(self, path_pattern: str) -> List[Card]:
        cards: List[Card] = []
        files = sorted(glob(path_pattern))
        print(f"[CardRepo] Found {len(files)} data files matching {path_pattern}:")
        for fn in files:
            basename = os.path.basename(fn)
            # derive expansion name
            if basename.endswith('.json.zst'):
                expansion = basename[:-len('.json.zst')]
                print(f"  → Detected compressed file: {fn!r}")
            else:
                expansion = os.path.splitext(basename)[0]
                print(f"  → Detected uncompressed file: {fn!r}")
            expansion = expansion.removesuffix("_pack")

            print(f"  → Loading file: {fn!r} as expansion '{expansion}'")

            raw_cards = self._load_file(fn)
            print(f"     contains {len(raw_cards)} raw cards")

            for raw in raw_cards:
                cards.append(Card(
                    text      = raw["text"],
                    card_type = raw["type"],
                    pick      = raw.get("pick", 1),
                    regions   = raw["regions"],
                    expansion = expansion
                ))
        print(f"[CardRepo] Total cards loaded: {len(cards)}\n")
        return cards

    def _load_file(self, fn: str) -> List[Dict]:
        if fn.lower().endswith('.json.zst'):
            data = Path(fn).read_bytes()
            dctx = zstd.ZstdDecompressor()
            txt = dctx.decompress(data).decode('utf-8')
            return json.loads(txt)
        else:
            with open(fn, encoding='utf-8') as f:
                return json.load(f)

    def load(self) -> List[Card]:
        return list(self._cards)

    def filter(
        self,
        card_type:  Optional[str]          = None,
        regions:    Optional[Dict[str,bool]] = None,
        expansions: Optional[List[str]]     = None
    ) -> List[Card]:
        cards = self._cards
        if card_type:
            cards = [c for c in cards if c.card_type == card_type]
        if regions:
            cards = [
                c for c in cards
                if any(regions.get(r, False) and c.regions.get(r, False)
                       for r in regions)
            ]
        if expansions:
            cards = [c for c in cards if c.expansion in expansions]
        return cards.copy()

    def print_stats(self) -> None:
        per_file = defaultdict(int)
        region_totals = defaultdict(int)
        for c in self._cards:
            per_file[c.expansion] += 1
            for region, allowed in c.regions.items():
                if allowed:
                    region_totals[region] += 1

        for exp, cnt in per_file.items():
            print(f"Loaded {cnt} cards from expansion '{exp}'")
        print("\nTotals by region:")
        for region, cnt in region_totals.items():
            print(f"  {region}: {cnt}")
        print(f"\nGrand total: {len(self._cards)} cards\n")

    def reload(self, path_pattern: Optional[str] = None) -> None:
        if path_pattern:
            self._path_pattern = path_pattern
        self._cards = self._load_all(self._path_pattern)

    def available_expansions(self) -> List[str]:
        return sorted({c.expansion for c in self._cards})

    def available_regions(self) -> List[str]:
        if not self._cards:
            return []
        return list(self._cards[0].regions.keys())
