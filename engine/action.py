import dataclasses

from .structs import LawType
from .structs import Phase
from .structs import Team
from .structs import Vote


@dataclasses.dataclass
class Action:
    turn: int
    phase: Phase
    player_index: int


@dataclasses.dataclass
class ChooseChancellorAction(Action):
    phase = Phase.CHOOSE_CHANCELLOR
    chancellor_index: int


@dataclasses.dataclass
class VoteAction(Action):
    phase = Phase.VOTE
    vote: Vote


@dataclasses.dataclass
class PresidentDiscardAction(Action):
    phase = Phase.PRESIDENT_DISCARD
    discarded_card: LawType


@dataclasses.dataclass
class ChancellorVetoAction(Action):
    phase = Phase.CHANCELLOR_VETO
    is_veto: bool


@dataclasses.dataclass
class PresidentVetoAction(Action):
    phase = Phase.PRESIDENT_VETO
    is_veto: bool


@dataclasses.dataclass
class ChancellorDiscardAction(Action):
    phase = Phase.CHANCELLOR_DISCARD
    discarded_card: LawType


@dataclasses.dataclass
class LawClaimAction(Action):
    phase = Phase.LAW_CLAIM
    received_cards: list[LawType] | None
    discarded_card: LawType | None


@dataclasses.dataclass
class TeamCheckAction(Action):
    phase = Phase.TEAM_CHECK
    target_index: int


@dataclasses.dataclass
class TeamClaimAction(Action):
    phase = Phase.TEAM_CLAIM
    team: Team


@dataclasses.dataclass
class ChooseOutOfOrderPresidentAction(Action):
    phase = Phase.CHOOSE_OUT_OF_ORDER_PRESIDENT
    out_of_order_president_index: int


@dataclasses.dataclass
class KillAction(Action):
    phase = Phase.KILL
    target_index: int
