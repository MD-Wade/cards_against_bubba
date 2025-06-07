from enum import Enum

class Phase(str, Enum):
    WAITING       = "waiting_for_players"
    DRAFT_PICKING = "draft_picking"
    SUBMISSIONS   = "submissions"
    JUDGING       = "judging"