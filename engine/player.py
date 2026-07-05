import dataclasses
import random
from typing import Any

from .action import Action
from .action import ChancellorDiscardAction
from .action import ChancellorVetoAction
from .action import ChooseChancellorAction
from .action import ChooseOutOfOrderPresidentAction
from .action import KillAction
from .action import LawClaimAction
from .action import PresidentDiscardAction
from .action import PresidentVetoAction
from .action import TeamCheckAction
from .action import TeamClaimAction
from .action import VoteAction
from .structs import LawType
from .structs import Phase
from .structs import Role
from .structs import State
from .structs import Team
from .structs import Vote


@dataclasses.dataclass
class Player:
    name: str

    def action(self, state: State) -> Action:
        raise NotImplementedError()


@dataclasses.dataclass
class DummyPlayer(Player):
    last_received_cards: list[LawType] | None = None
    last_discarded_card: LawType | None = None

    def action(self, state: State) -> Action:
        assert state.self_index is not None
        assert isinstance(state.self_index, int)

        action_kwargs: dict[str, Any] = {
            "turn": state.turn,
            "phase": state.phase,
            "player_index": state.self_index,
        }

        match state.phase:
            case Phase.CHOOSE_CHANCELLOR:
                assert state.self_index == state.current_president
                candidates = []
                for index in state.alive_players():
                    if index == state.previous_president:
                        continue
                    if index == state.previous_chancellor:
                        continue
                    if index == state.current_president:
                        continue
                    candidates.append(index)
                return ChooseChancellorAction(
                    chancellor_index=random.choice(candidates),
                    **action_kwargs,
                )

            case Phase.VOTE:
                if random.random() < 0.75:
                    vote = Vote.YES
                else:
                    vote = Vote.NO
                return VoteAction(
                    vote=vote,
                    **action_kwargs,
                )

            case Phase.PRESIDENT_DISCARD:
                assert state.self_index == state.current_president
                assert state.president_choice_cards is not None
                has_blue = LawType.BLUE in state.president_choice_cards
                has_red = LawType.RED in state.president_choice_cards

                assert state.self_index is not None
                match state.roles[state.self_index]:
                    case Role.LIBERAL:
                        discarded_card = LawType.RED if has_red else LawType.BLUE
                    case Role.FASCIST:
                        if random.random() < 0.9:
                            discarded_card = LawType.BLUE if has_blue else LawType.RED
                        else:
                            discarded_card = LawType.RED if has_red else LawType.BLUE
                    case Role.HITLER:
                        if random.random() < 0.2:
                            discarded_card = LawType.RED if has_red else LawType.BLUE
                        else:
                            discarded_card = LawType.BLUE if has_blue else LawType.RED
                    case _:
                        assert False

                self.last_received_cards = state.president_choice_cards
                # noinspection PyUnboundLocalVariable
                self.last_discarded_card = discarded_card

                return PresidentDiscardAction(
                    discarded_card=discarded_card,
                    **action_kwargs,
                )

            case Phase.CHANCELLOR_VETO:
                assert state.self_index == state.current_chancellor
                assert state.chancellor_choice_cards is not None
                has_blue = LawType.BLUE in state.chancellor_choice_cards
                assert state.self_index is not None
                is_veto = state.roles[state.self_index] == Role.LIBERAL and not has_blue

                return ChancellorVetoAction(
                    is_veto=is_veto,
                    **action_kwargs,
                )

            case Phase.PRESIDENT_VETO:
                assert state.self_index == state.current_president
                assert state.chancellor_choice_cards is not None
                has_blue = LawType.BLUE in state.chancellor_choice_cards
                assert state.self_index is not None
                is_veto = state.roles[state.self_index] == Role.LIBERAL and not has_blue

                return PresidentVetoAction(
                    is_veto=is_veto,
                    **action_kwargs,
                )

            case Phase.CHANCELLOR_DISCARD:
                assert state.self_index == state.current_chancellor
                assert state.chancellor_choice_cards is not None
                has_blue = LawType.BLUE in state.chancellor_choice_cards
                has_red = LawType.RED in state.chancellor_choice_cards

                assert state.self_index is not None
                match state.roles[state.self_index]:
                    case Role.LIBERAL:
                        discarded_card = LawType.RED if has_red else LawType.BLUE
                    case Role.FASCIST:
                        if random.random() < 0.9:
                            discarded_card = LawType.BLUE if has_blue else LawType.RED
                        else:
                            discarded_card = LawType.RED if has_red else LawType.BLUE
                    case Role.HITLER:
                        if random.random() < 0.2:
                            discarded_card = LawType.RED if has_red else LawType.BLUE
                        else:
                            discarded_card = LawType.BLUE if has_blue else LawType.RED
                    case _:
                        assert False

                self.last_received_cards = state.chancellor_choice_cards
                # noinspection PyUnboundLocalVariable
                self.last_discarded_card = discarded_card

                return ChancellorDiscardAction(
                    discarded_card=discarded_card,
                    **action_kwargs,
                )

            case Phase.LAW_CLAIM:
                return LawClaimAction(
                    received_cards=self.last_received_cards,
                    discarded_card=self.last_discarded_card,
                    **action_kwargs,
                )

            case Phase.TEAM_CHECK:
                previous_checks = [x.target_index for x in state.team_claims]
                candidates = []
                for index in state.alive_players():
                    if index == state.self_index:
                        continue
                    if index in previous_checks:
                        continue
                    candidates.append(index)
                return TeamCheckAction(
                    target_index=random.choice(candidates),
                    **action_kwargs,
                )

            case Phase.TEAM_CLAIM:
                team = state.team_claims[-1].real_team
                assert team is not None

                if not state.roles[state.self_index] == Role.LIBERAL:
                    if random.random() < 0.5:
                        if team == Team.LIBERAL:
                            team = Team.FASCIST
                        else:
                            team = Team.LIBERAL

                return TeamClaimAction(
                    team=team,
                    **action_kwargs,
                )

            case Phase.CHOOSE_OUT_OF_ORDER_PRESIDENT:
                candidates = []
                for index in state.alive_players():
                    if index == state.self_index:
                        continue
                    candidates.append(index)
                return ChooseOutOfOrderPresidentAction(
                    out_of_order_president_index=random.choice(candidates),
                    **action_kwargs,
                )

            case Phase.KILL:
                candidates = []
                for index in state.alive_players():
                    if index == state.self_index:
                        continue
                    if state.roles[state.self_index] == Role.FASCIST:
                        if state.roles[index] != Role.LIBERAL:
                            continue
                    candidates.append(index)
                return KillAction(
                    target_index=random.choice(candidates),
                    **action_kwargs,
                )

            case Phase.GAME_ENDED:
                print(f"Player {self.name} accepts game end event")
                pass

            case _:
                assert False

        assert False
