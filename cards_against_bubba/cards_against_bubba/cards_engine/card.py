from dataclasses import dataclass
from typing import Literal, Mapping, Optional

@dataclass(frozen=True)
class Card:
    text: str
    card_type: Literal["prompt", "response"]
    pick: int
    regions: Mapping[str, bool]
    expansion: Optional[str] = None