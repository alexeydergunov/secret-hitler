import dataclasses
from enum import Enum
from typing import Any


class EnumParent(Enum):
    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name


class LawType(EnumParent):
    RED = 1
    BLUE = 2

    def __repr__(self) -> str:
        return self.name


class Team(EnumParent):
    LIBERAL = 1
    FASCIST = 2


class Role(EnumParent):
    UNKNOWN = 0
    LIBERAL = 1
    FASCIST = 2
    HITLER = 3


class Phase(EnumParent):
    CHOOSE_CHANCELLOR = 0
    VOTE = 1
    PRESIDENT_DISCARD = 2
    CHANCELLOR_VETO = 3
    PRESIDENT_VETO = 4
    CHANCELLOR_DISCARD = 5
    LAW_CLAIM = 6
    TEAM_CHECK = 7
    TEAM_CLAIM = 8
    DECK_CHECK = 9
    CHOOSE_OUT_OF_ORDER_PRESIDENT = 10
    KILL = 11
    GAME_ENDED = 12


class Vote(EnumParent):
    UNDECIDED = 0
    NO = 1
    YES = 2


class WinReason(EnumParent):
    LIBERAL_LAWS = 0
    HITLER_KILLED = 1
    FASCIST_LAWS = 2
    FASCIST_MAJORITY = 3
    HITLER_CHANCELLOR = 4


@dataclasses.dataclass
class RoundVote:
    turn: int
    president_index: int
    chancellor_index: int
    votes: list[Vote]


@dataclasses.dataclass
class LawClaim:
    turn: int
    player_index: int
    received_cards: list[LawType] | None
    discarded_card: LawType | None
    real_received_cards: list[LawType] | None
    real_discarded_card: LawType | None


@dataclasses.dataclass
class TeamClaim:
    turn: int
    president_index: int
    target_index: int
    team: Team | None
    real_team: Team | None


@dataclasses.dataclass
class DeckClaim:
    turn: int
    president_index: int
    top_three_cards: list[LawType] | None
    real_top_three_cards: list[LawType] | None


@dataclasses.dataclass
class State:
    player_count: int
    self_index: int | None
    roles: list[Role]
    deck: list[LawType] | None
    deck_size: int
    accepted_laws: list[LawType]
    round_skip_count: int
    previous_president: int | None
    previous_chancellor: int | None
    current_president: int
    current_chancellor: int | None
    is_out_of_order_presidency: bool
    not_hitler_players: list[int]
    killed_players: list[int]
    turn: int
    phase: Phase
    last_shuffle_turn: int
    president_choice_cards: list[LawType] | None
    chancellor_choice_cards: list[LawType] | None
    round_votes: list[RoundVote]
    law_claims: list[LawClaim]
    team_claims: list[TeamClaim]
    deck_claim: DeckClaim | None
    winner_team: Team | None
    win_reason: WinReason | None

    def action_kwargs(self) -> dict[str, Any]:
        return {
            "turn": self.turn,
            "player_index": self.self_index,
        }

    def liberal_score(self) -> int:
        return len([x for x in self.accepted_laws if x == LawType.BLUE])

    def fascist_score(self) -> int:
        return len([x for x in self.accepted_laws if x == LawType.RED])

    def last_accepted_law(self) -> LawType | None:
        if len(self.accepted_laws) == 0:
            return None
        return self.accepted_laws[-1]

    def is_team_check_active(self) -> bool:
        if self.last_accepted_law() == LawType.RED:
            if self.player_count in {7, 8} and self.fascist_score() == 2:
                return True
            if self.player_count in {9, 10} and self.fascist_score() in {1, 2}:
                return True
        return False

    def is_deck_check_active(self) -> bool:
        if self.last_accepted_law() == LawType.RED:
            if self.player_count in {5, 6} and self.fascist_score() == 3:
                return True
        return False

    def is_choose_out_of_order_president_active(self) -> bool:
        if self.last_accepted_law() == LawType.RED:
            if self.player_count in {7, 8, 9, 10} and self.fascist_score() == 3:
                return True
        return False

    def is_kill_active(self) -> bool:
        if self.last_accepted_law() == LawType.RED:
            if self.fascist_score() in {4, 5}:
                return True
        return False

    def is_veto_active(self) -> bool:
        return self.fascist_score() == 5

    def top_three_cards(self) -> list[LawType]:
        assert self.deck is not None
        assert len(self.deck) >= 3
        return [
            self.deck[-1],
            self.deck[-2],
            self.deck[-3],
        ]

    def alive_players(self) -> list[int]:
        return [x for x in range(self.player_count) if x not in self.killed_players]

    def hitler_index(self) -> int:
        return self.roles.index(Role.HITLER)

    def hitler_is_chancellor(self) -> bool:
        return self.current_chancellor == self.hitler_index()

    def is_fascist_majority(self) -> bool:
        alive_players = self.alive_players()
        liberal_count = len([i for i in alive_players if self.roles[i] == Role.LIBERAL])
        fascist_count = len([i for i in alive_players if self.roles[i] in {Role.FASCIST, Role.HITLER}])
        return fascist_count > liberal_count

    def get_team(self, player_index: int) -> Team:
        assert 0 <= player_index < self.player_count
        if self.roles[player_index] == Role.LIBERAL:
            return Team.LIBERAL
        if self.roles[player_index] in {Role.FASCIST, Role.HITLER}:
            return Team.FASCIST
        else:
            assert False
