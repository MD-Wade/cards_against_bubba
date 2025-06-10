from dataclasses import dataclass
from typing import Literal, Mapping, Optional, List
import re

@dataclass(frozen=True)
class Card:
    text: str
    card_type: Literal["prompt", "response"]
    pick: int
    regions: Mapping[str, bool]
    expansion: Optional[str] = None

    @property
    def num_blanks(self) -> int:
        """Returns the number of blank slots (underscores) in the text."""
        return len(re.findall(r'_{3,}', self.text))  # matches ___, ____, etc.

    @property
    def has_blanks(self) -> bool:
        """True if the card text has at least one blank."""
        return self.num_blanks > 0

    import re

    def format_prompt(self, responses: List[str]) -> str:
        def _strip_single_terminal_punct(text):
            if not text:
                return text
            if len(text) > 2 and text[-3:] == "...":
                return text
            if len(text) > 1 and text[-2:] in ("?!", "!?"):
                return text
            if text[-1] in ".!?":
                if len(text) == 1 or text[-2] not in ".!?":
                    return text[:-1]
            return text

        n = self.num_blanks
        out = self.text

        if n > 0:
            def replacer(match):
                idx = replacer.idx
                replacer.idx += 1
                if idx < len(responses):
                    resp = _strip_single_terminal_punct(responses[idx])
                    # If the previous char is not a terminal punctuation,
                    # and resp starts with "The"/"A"/"An", lowercase it
                    start = match.start()
                    prev_char = self.text[start-1] if start > 0 else ""
                    if prev_char not in ".!?" and re.match(r"^(The|A|An)\b", resp):
                        resp = resp[0].lower() + resp[1:]
                    return f"**{resp}**"
                return match.group(0)
            replacer.idx = 0
            out = re.sub(r'_{3,}', replacer, out)
            return out
        else:
            resp_text = " ".join(f"**{resp}**" for resp in responses)
            if resp_text:
                out = f"{out} {resp_text}"
            return out