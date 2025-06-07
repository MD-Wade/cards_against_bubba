import json
from glob import glob
from collections import defaultdict
from typing import List, Optional, Dict
from card import Card

class CardRepository:
    def __init__(self, path_pattern: str = "data/cards/*.json"):
        self.path_pattern = path_pattern
        self._cards: Optional[List[Card]] = None

    def load(self) -> List[Card]:
        """Load & cache all cards (no printing)."""
        if self._cards is not None:
            return self._cards

        all_cards: List[Card] = []
        for fn in glob(self.path_pattern):
            with open(fn, encoding="utf-8") as f:
                raw_cards = json.load(f)
            for raw in raw_cards:
                all_cards.append(Card(
                    text      = raw["text"],
                    card_type = raw["type"],
                    pick      = raw.get("pick", 1),
                    regions   = raw["regions"],
                    expansion = raw.get("expansion"),
                ))

        self._cards = all_cards
        return all_cards

    def print_stats(self) -> None:
        """Print load stats per file and totals per region."""
        region_totals: Dict[str, int] = defaultdict(int)
        per_file_counts: Dict[str, int] = {}

        # First, re-parse each file just to get per-file counts
        for fn in glob(self.path_pattern):
            with open(fn, encoding="utf-8") as f:
                raws = json.load(f)
            per_file_counts[fn] = len(raws)
            for raw in raws:
                for region, allowed in raw["regions"].items():
                    if allowed:
                        region_totals[region] += 1

        # Print per-file
        for fn, count in per_file_counts.items():
            print(f"Loaded {count} cards from {fn}")

        # Print region totals
        print("\nTotals by region:")
        for region, count in region_totals.items():
            print(f"  {region}: {count}")

        # Grand total
        print(f"\nGrand total: {len(self.load())} cards\n")

    def filter(
        self,
        *,
        card_type: Optional[str]   = None,
        regions:   Optional[Dict[str, bool]] = None,
        expansion: Optional[str]   = None,
    ) -> List[Card]:
        cards = self.load()
        if card_type:
            cards = [c for c in cards if c.card_type == card_type]
        if regions:
            cards = [
                c for c in cards
                if any(regions.get(r) and c.regions.get(r) for r in regions)
            ]
        if expansion:
            cards = [c for c in cards if c.expansion == expansion]
        return cards

    def reload(self) -> None:
        """Clear cache so that next load() re-reads all JSON files."""
        self._cards = None
