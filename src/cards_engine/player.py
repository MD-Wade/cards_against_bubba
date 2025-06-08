from dataclasses import dataclass, field
from typing import List, Optional
from .card import Card

@dataclass
class Player:
    id: str
    name: str
    hand: List[Card] = field(default_factory=list)
    score: int = 0