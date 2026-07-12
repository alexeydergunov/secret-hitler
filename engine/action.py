import dataclasses

from .structs import LawType
from .structs import Phase
from .structs import Team
from .structs import Vote


@dataclasses.dataclass(kw_only=True)
class Action:
    turn: int
    phase: Phase
    player_index: int


@dataclasses.dataclass(kw_only=True)
class ChooseChancellorAction(Action):
    phase: Phase = Phase.CHOOSE_CHANCELLOR
    chancellor_index: int


@dataclasses.dataclass(kw_only=True)
class VoteAction(Action):
    phase: Phase = Phase.VOTE
    vote: Vote


@dataclasses.dataclass(kw_only=True)
class PresidentDiscardAction(Action):
    phase: Phase = Phase.PRESIDENT_DISCARD
    discarded_card: LawType


@dataclasses.dataclass(kw_only=True)
class ChancellorVetoAction(Action):
    phase: Phase = Phase.CHANCELLOR_VETO
    is_veto: bool


@dataclasses.dataclass(kw_only=True)
class PresidentVetoAction(Action):
    phase: Phase = Phase.PRESIDENT_VETO
    is_veto: bool


@dataclasses.dataclass(kw_only=True)
class ChancellorDiscardAction(Action):
    phase: Phase = Phase.CHANCELLOR_DISCARD
    discarded_card: LawType


@dataclasses.dataclass(kw_only=True)
class LawClaimAction(Action):
    phase: Phase = Phase.LAW_CLAIM
    received_cards: list[LawType] | None
    discarded_card: LawType | None


@dataclasses.dataclass(kw_only=True)
class TeamCheckAction(Action):
    phase: Phase = Phase.TEAM_CHECK
    target_index: int


@dataclasses.dataclass(kw_only=True)
class TeamClaimAction(Action):
    phase: Phase = Phase.TEAM_CLAIM
    team: Team


@dataclasses.dataclass(kw_only=True)
class DeckCheckAction(Action):
    phase: Phase = Phase.DECK_CHECK
    top_three_cards: list[LawType]


@dataclasses.dataclass(kw_only=True)
class ChooseOutOfOrderPresidentAction(Action):
    phase: Phase = Phase.CHOOSE_OUT_OF_ORDER_PRESIDENT
    out_of_order_president_index: int


@dataclasses.dataclass(kw_only=True)
class KillAction(Action):
    phase: Phase = Phase.KILL
    target_index: int
