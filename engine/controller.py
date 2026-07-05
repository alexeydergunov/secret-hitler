import copy
import random
import time

from .action import Action
from .action import ChancellorDiscardAction
from .action import ChancellorVetoAction
from .action import ChooseChancellorAction
from .action import ChooseOutOfOrderPresidentAction
from .action import DeckCheckAction
from .action import KillAction
from .action import LawClaimAction
from .action import PresidentDiscardAction
from .action import PresidentVetoAction
from .action import TeamCheckAction
from .action import TeamClaimAction
from .action import VoteAction
from .player import Player
from .structs import DeckClaim
from .structs import LawClaim
from .structs import LawType
from .structs import Phase
from .structs import Role
from .structs import RoundVote
from .structs import State
from .structs import Team
from .structs import TeamClaim
from .structs import Vote
from .structs import WinReason


class Controller:
    players: list[Player]
    all_states: list[State]
    all_actions: list[Action]

    def __init__(self, players: list[Player]):
        self.init_new_game(players=players)

    @classmethod
    def get_shuffled_roles(cls, player_count: int) -> list[Role]:
        roles: list[Role] = []
        for i in range(player_count // 2 - 1):
            roles.append(Role.FASCIST)
        roles.append(Role.HITLER)
        while len(roles) < player_count:
            roles.append(Role.LIBERAL)

        random.shuffle(roles)
        return roles

    @classmethod
    def reshuffle_deck(cls, state: State):
        assert state.deck is not None
        assert len(state.deck) == state.deck_size
        assert state.deck_size <= 2

        red_count = 11 - state.fascist_score()
        blue_count = 6 - state.liberal_score()
        deck = [LawType.RED] * red_count + [LawType.BLUE] * blue_count
        random.shuffle(deck)

        state.deck = deck
        state.deck_size = len(deck)
        state.last_shuffle_turn = state.turn

    @classmethod
    def choose_next_president(cls, state: State):
        if state.is_out_of_order_presidency:
            assert state.previous_president is not None
            president = state.previous_president
            state.is_out_of_order_presidency = False
        else:
            president = state.current_president

        while True:
            president = (president + 1) % state.player_count
            if president not in state.killed_players:
                break

        state.current_president = president

    @classmethod
    def next_turn(cls, state: State):
        assert state.current_chancellor is not None
        previous_president: int = state.current_president
        previous_chancellor: int = state.current_chancellor
        cls.choose_next_president(state=state)
        state.current_chancellor = None
        state.previous_president = previous_president
        if len(state.alive_players()) <= 5:
            state.previous_chancellor = None
        else:
            state.previous_chancellor = previous_chancellor

        state.president_choice_cards = None
        state.chancellor_choice_cards = None

        state.phase = Phase.CHOOSE_CHANCELLOR
        state.turn += 1
        print(f"Going to turn {state.turn}")

    @classmethod
    def round_skip(cls, state: State):
        state.round_skip_count += 1
        if state.round_skip_count < 3:
            cls.next_turn(state=state)
        else:
            cls.choose_next_president(state=state)
            state.current_chancellor = None
            state.previous_president = None
            state.previous_chancellor = None
            state.president_choice_cards = None
            state.chancellor_choice_cards = None
            assert state.deck is not None
            new_law = state.deck.pop()
            state.deck_size -= 1
            state.accepted_laws.append(new_law)
            if state.deck_size <= 2:
                cls.reshuffle_deck(state=state)
            if state.liberal_score() == 5:
                state.winner_team = Team.LIBERAL
                state.win_reason = WinReason.LIBERAL_LAWS
                state.phase = Phase.GAME_ENDED
            elif state.fascist_score() == 6:
                state.winner_team = Team.FASCIST
                state.win_reason = WinReason.FASCIST_LAWS
                state.phase = Phase.GAME_ENDED
            else:
                state.phase = Phase.CHOOSE_CHANCELLOR
                state.turn += 1
            state.round_skip_count = 0

    @classmethod
    def hide_from_player(cls, source_state: State, player_index: int, player_role: Role) -> State:
        state = copy.deepcopy(source_state)

        state.self_index = player_index

        not_knowing_roles = {Role.LIBERAL}
        if state.player_count >= 7:
            not_knowing_roles.add(Role.HITLER)
        if player_role in not_knowing_roles:
            for i in range(len(state.roles)):
                if i != player_index:
                    state.roles[i] = Role.UNKNOWN

        state.deck = None

        if state.president_choice_cards is not None:
            if player_index != state.current_president:
                state.president_choice_cards = None

        if state.chancellor_choice_cards is not None:
            if player_index not in {state.current_president, state.current_chancellor}:
                state.chancellor_choice_cards = None

        for law_claim in state.law_claims:
            if law_claim.player_index != player_index:
                law_claim.real_received_cards = None
                law_claim.real_discarded_card = None

        for team_claim in state.team_claims:
            if team_claim.president_index != player_index:
                team_claim.real_team = None

        if state.deck_claim is not None:
            if state.deck_claim.president_index != player_index:
                state.deck_claim.real_top_three_cards = None

        return state

    def init_new_game(self, players: list[Player]):
        random.seed(time.time_ns())

        player_count = len(players)
        assert 5 <= player_count <= 10
        roles = self.get_shuffled_roles(player_count=player_count)
        first_president = random.randrange(0, player_count)
        print(f"Roles: {roles}, first president: {first_president}")

        deck = [LawType.RED] * 11 + [LawType.BLUE] * 6
        random.shuffle(deck)

        initial_state = State(
            player_count=player_count,
            self_index=None,
            roles=roles,
            deck=deck,
            deck_size=len(deck),
            accepted_laws=[],
            round_skip_count=0,
            previous_president=None,
            previous_chancellor=None,
            current_president=first_president,
            current_chancellor=None,
            is_out_of_order_presidency=False,
            not_hitler_players=[],
            killed_players=[],
            turn=1,
            phase=Phase.CHOOSE_CHANCELLOR,
            last_shuffle_turn=0,
            president_choice_cards=None,
            chancellor_choice_cards=None,
            round_votes=[],
            law_claims=[],
            team_claims=[],
            deck_claim=None,
            winner_team=None,
            win_reason=None,
        )

        self.players = players
        self.all_states = [initial_state]
        self.all_actions = []

    def run_game(self):
        while True:
            current_state = self.all_states[-1]
            if current_state.phase == Phase.GAME_ENDED:
                print(f"Game ended with score: "
                      f"Blue {current_state.liberal_score()}, Red {current_state.fascist_score()}, "
                      f"Winner: {current_state.winner_team}, Win reason: {current_state.win_reason}")
                break
            self.preform_next_turn()

    def preform_next_turn(self):
        current_state = copy.deepcopy(self.all_states[-1])
        print()
        print(f"Current turn {current_state.turn}, phase {current_state.phase}, "
              f"score: Blue {current_state.liberal_score()}, Red {current_state.fascist_score()}")

        actions: list[Action] = []
        for player_index in current_state.alive_players():
            action = self.ask_player(current_state, player_index=player_index)
            if action is not None:
                actions.append(action)

        print(f"Got {len(actions)} actions")
        new_state: State = self.apply_actions(current_state=current_state, actions=actions)

        self.all_states.append(new_state)
        self.all_actions.extend(actions)

        for player_index, player in enumerate(self.players):
            player.state = self.hide_from_player(
                source_state=new_state,
                player_index=player_index,
                player_role=current_state.roles[player_index],
            )

    @classmethod
    def apply_actions(cls, current_state: State, actions: list[Action]) -> State:
        for action in actions:
            assert action.turn == current_state.turn
            assert action.phase == current_state.phase

        new_state = copy.deepcopy(current_state)

        match current_state.phase:
            case Phase.CHOOSE_CHANCELLOR:
                assert len(actions) == 1
                action = actions[0]
                assert isinstance(action, ChooseChancellorAction)
                print(
                    f"Player {action.player_index} action {action.phase}, chancellor_index = {action.chancellor_index}")
                assert action.player_index == current_state.current_president
                assert action.chancellor_index != current_state.current_president
                assert action.chancellor_index != current_state.previous_president
                assert action.chancellor_index != current_state.previous_chancellor
                assert action.chancellor_index not in current_state.killed_players

                new_state.current_chancellor = action.chancellor_index
                new_state.phase = Phase.VOTE

            case Phase.VOTE:
                alive_players = current_state.alive_players()
                assert len(actions) == len(alive_players)
                assert current_state.current_chancellor is not None
                votes = [Vote.UNDECIDED] * current_state.player_count

                for action in actions:
                    assert isinstance(action, VoteAction)
                    print(f"Player {action.player_index} phase {action.phase}, vote = {action.vote}")
                    assert votes[action.player_index] == Vote.UNDECIDED
                    votes[action.player_index] = action.vote
                new_state.round_votes.append(RoundVote(
                    turn=current_state.turn,
                    president_index=current_state.current_president,
                    chancellor_index=current_state.current_chancellor,
                    votes=votes,
                ))

                if len([x for x in votes if x == Vote.YES]) > len(alive_players) // 2:
                    if current_state.fascist_score() >= 3 and current_state.hitler_is_chancellor():
                        new_state.winner_team = Team.FASCIST
                        new_state.win_reason = WinReason.HITLER_CHANCELLOR
                        new_state.phase = Phase.GAME_ENDED
                    else:
                        if current_state.fascist_score() >= 3:
                            if current_state.current_chancellor not in new_state.not_hitler_players:
                                new_state.not_hitler_players.append(current_state.current_chancellor)
                        new_state.phase = Phase.PRESIDENT_DISCARD
                        assert new_state.deck is not None
                        assert new_state.deck_size >= 3
                        president_choice_cards: list[LawType] = []
                        for i in range(3):
                            president_choice_cards.append(new_state.deck.pop())
                        random.shuffle(president_choice_cards)
                        new_state.president_choice_cards = president_choice_cards
                        new_state.deck_size -= 3
                        if new_state.deck_size <= 2:
                            cls.reshuffle_deck(state=new_state)
                        new_state.round_skip_count = 0
                else:
                    cls.round_skip(state=new_state)

            case Phase.PRESIDENT_DISCARD:
                assert len(actions) == 1
                action = actions[0]
                assert isinstance(action, PresidentDiscardAction)
                print(f"Player {action.player_index} phase {action.phase}, discarded_card = {action.discarded_card}")

                assert action.player_index == current_state.current_president
                assert current_state.president_choice_cards is not None
                assert len(current_state.president_choice_cards) == 3
                assert action.discarded_card in current_state.president_choice_cards

                assert new_state.president_choice_cards is not None
                assert new_state.chancellor_choice_cards is None
                chancellor_choice_cards = copy.deepcopy(current_state.president_choice_cards)
                chancellor_choice_cards.remove(action.discarded_card)
                random.shuffle(chancellor_choice_cards)
                new_state.chancellor_choice_cards = chancellor_choice_cards

                if current_state.is_veto_active():
                    new_state.phase = Phase.CHANCELLOR_VETO
                else:
                    new_state.phase = Phase.CHANCELLOR_DISCARD

            case Phase.CHANCELLOR_VETO:
                assert current_state.is_veto_active()
                assert len(actions) == 1
                action = actions[0]
                assert isinstance(action, ChancellorVetoAction)
                print(f"Player {action.player_index} phase {action.phase}, is_veto = {action.is_veto}")
                assert current_state.chancellor_choice_cards is not None
                assert len(current_state.chancellor_choice_cards) == 2

                if not action.is_veto:
                    new_state.phase = Phase.CHANCELLOR_DISCARD
                else:
                    new_state.phase = Phase.PRESIDENT_VETO

            case Phase.PRESIDENT_VETO:
                assert current_state.is_veto_active()
                assert len(actions) == 1
                action = actions[0]
                assert isinstance(action, PresidentVetoAction)
                print(f"Player {action.player_index} phase {action.phase}, is_veto = {action.is_veto}")
                assert current_state.chancellor_choice_cards is not None
                assert len(current_state.chancellor_choice_cards) == 2

                if not action.is_veto:
                    new_state.phase = Phase.CHANCELLOR_DISCARD
                else:
                    cls.round_skip(state=new_state)

            case Phase.CHANCELLOR_DISCARD:
                assert len(actions) == 1
                action = actions[0]
                assert isinstance(action, ChancellorDiscardAction)
                print(f"Player {action.player_index} phase {action.phase}, discarded_card = {action.discarded_card}")
                assert action.player_index == current_state.current_chancellor
                assert current_state.chancellor_choice_cards is not None
                assert len(current_state.chancellor_choice_cards) == 2
                assert action.discarded_card in current_state.chancellor_choice_cards
                assert new_state.chancellor_choice_cards is not None

                remained_cards = copy.deepcopy(current_state.chancellor_choice_cards)
                remained_cards.remove(action.discarded_card)
                assert len(remained_cards) == 1
                new_law = remained_cards[0]
                new_state.accepted_laws.append(new_law)

                if new_state.liberal_score() == 5:
                    new_state.winner_team = Team.LIBERAL
                    new_state.win_reason = WinReason.LIBERAL_LAWS
                    new_state.phase = Phase.GAME_ENDED
                elif new_state.fascist_score() == 6:
                    new_state.winner_team = Team.FASCIST
                    new_state.win_reason = WinReason.FASCIST_LAWS
                    new_state.phase = Phase.GAME_ENDED
                else:
                    new_state.phase = Phase.LAW_CLAIM

            case Phase.LAW_CLAIM:
                assert len(actions) == 2
                actions_by_index = {a.player_index: a for a in actions}
                assert actions_by_index.keys() == {current_state.current_president, current_state.current_chancellor}
                assert current_state.president_choice_cards is not None
                assert current_state.chancellor_choice_cards is not None
                assert len(current_state.president_choice_cards) == 3
                assert len(current_state.chancellor_choice_cards) == 2
                for player_index in [current_state.current_president, current_state.current_chancellor]:
                    assert player_index is not None
                    action = actions_by_index[player_index]
                    assert isinstance(action, LawClaimAction)
                    print(f"Player {action.player_index} phase {action.phase}, "
                          f"received_cards = {action.received_cards}, "
                          f"discarded_card = {action.discarded_card}")
                    if player_index == current_state.current_president:
                        real_received_cards = current_state.president_choice_cards
                        tmp = copy.deepcopy(real_received_cards)
                        for card in current_state.chancellor_choice_cards:
                            assert card in tmp
                            tmp.remove(card)
                        real_discarded_card = tmp[0]
                    elif player_index == current_state.current_chancellor:
                        real_received_cards = current_state.chancellor_choice_cards
                        tmp = copy.deepcopy(real_received_cards)
                        card = current_state.last_accepted_law()
                        assert card is not None
                        assert card in tmp
                        tmp.remove(card)
                        real_discarded_card = tmp[0]
                    else:
                        assert False

                    assert player_index is not None
                    new_state.law_claims.append(LawClaim(
                        turn=current_state.turn,
                        player_index=player_index,
                        received_cards=action.received_cards,
                        discarded_card=action.discarded_card,
                        real_received_cards=real_received_cards,
                        real_discarded_card=real_discarded_card,
                    ))
                if new_state.is_team_check_active():
                    new_state.phase = Phase.TEAM_CHECK
                elif new_state.is_deck_check_active():
                    new_state.deck_claim = DeckClaim(
                        turn=current_state.turn,
                        president_index=current_state.current_president,
                        top_three_cards=None,
                        real_top_three_cards=current_state.top_three_cards(),
                    )
                    new_state.phase = Phase.DECK_CHECK
                elif new_state.is_choose_out_of_order_president_active():
                    new_state.phase = Phase.CHOOSE_OUT_OF_ORDER_PRESIDENT
                elif new_state.is_kill_active():
                    new_state.phase = Phase.KILL
                else:
                    cls.next_turn(state=new_state)

            case Phase.TEAM_CHECK:
                assert len(actions) == 1
                action = actions[0]
                assert isinstance(action, TeamCheckAction)
                print(f"Player {action.player_index} phase {action.phase}, target_index = {action.target_index}")
                assert action.player_index == current_state.current_president
                assert action.target_index not in current_state.killed_players
                for team_claim in current_state.team_claims:
                    assert action.target_index != team_claim.target_index
                new_state.team_claims.append(TeamClaim(
                    turn=current_state.turn,
                    president_index=current_state.current_president,
                    target_index=action.target_index,
                    team=None,
                    real_team=current_state.get_team(player_index=action.target_index),
                ))
                new_state.phase = Phase.TEAM_CLAIM

            case Phase.TEAM_CLAIM:
                assert len(actions) == 1
                action = actions[0]
                assert isinstance(action, TeamClaimAction)
                print(f"Player {action.player_index} phase {action.phase}, team = {action.team}")
                assert action.player_index == current_state.current_president
                last_claim = new_state.team_claims[-1]
                assert last_claim.turn == current_state.turn
                last_claim.team = action.team
                cls.next_turn(state=new_state)

            case Phase.DECK_CHECK:
                assert len(actions) == 1
                action = actions[0]
                assert isinstance(action, DeckCheckAction)
                print(f"Player {action.player_index} phase {action.phase}, top_three_cards = {action.top_three_cards}")
                assert action.player_index == current_state.current_president
                assert len(action.top_three_cards) == 3
                assert current_state.deck_claim is not None
                new_state.deck_claim.top_three_cards = action.top_three_cards
                cls.next_turn(state=new_state)

            case Phase.CHOOSE_OUT_OF_ORDER_PRESIDENT:
                assert len(actions) == 1
                action = actions[0]
                assert isinstance(action, ChooseOutOfOrderPresidentAction)
                print(f"Player {action.player_index} phase {action.phase}, "
                      f"out_of_order_president_index = {action.out_of_order_president_index}")
                assert action.out_of_order_president_index != current_state.current_president
                assert action.out_of_order_president_index not in current_state.killed_players
                cls.next_turn(state=new_state)
                new_state.is_out_of_order_presidency = True
                new_state.current_president = action.out_of_order_president_index

            case Phase.KILL:
                assert len(actions) == 1
                action = actions[0]
                assert isinstance(action, KillAction)
                print(f"Player {action.player_index} phase {action.phase}, target_index = {action.target_index}")
                assert action.target_index != current_state.current_president
                assert action.target_index not in current_state.killed_players
                new_state.killed_players.append(action.target_index)
                if action.target_index == current_state.hitler_index():
                    new_state.winner_team = Team.LIBERAL
                    new_state.win_reason = WinReason.HITLER_KILLED
                    new_state.phase = Phase.GAME_ENDED
                elif new_state.is_fascist_majority():
                    new_state.winner_team = Team.FASCIST
                    new_state.win_reason = WinReason.FASCIST_MAJORITY
                    new_state.phase = Phase.GAME_ENDED
                else:
                    cls.next_turn(state=new_state)

            case Phase.GAME_ENDED:
                assert len(actions) == 0
                assert current_state.winner_team is not None
                print(f"Game ended in {current_state.turn} turns, "
                      f"winner is team {current_state.winner_team}, "
                      f"win reason {current_state.win_reason}")

            case _:
                assert False

        return new_state

    def ask_player(self, current_state: State, player_index: int) -> Action | None:
        match current_state.phase:
            case Phase.CHOOSE_CHANCELLOR:
                if player_index != current_state.current_president:
                    return None
            case Phase.VOTE:
                pass
            case Phase.PRESIDENT_DISCARD:
                if player_index != current_state.current_president:
                    return None
            case Phase.CHANCELLOR_VETO:
                if player_index != current_state.current_chancellor:
                    return None
                if not current_state.is_veto_active():
                    return None
            case Phase.PRESIDENT_VETO:
                if player_index != current_state.current_president:
                    return None
                if not current_state.is_veto_active():
                    return None
            case Phase.CHANCELLOR_DISCARD:
                if player_index != current_state.current_chancellor:
                    return None
            case Phase.LAW_CLAIM:
                if player_index not in {current_state.current_president, current_state.current_chancellor}:
                    return None
            case Phase.TEAM_CHECK | Phase.TEAM_CLAIM:
                if player_index != current_state.current_president:
                    return None
                if not current_state.is_team_check_active():
                    return None
            case Phase.DECK_CHECK:
                if player_index != current_state.current_president:
                    return None
                if not current_state.is_deck_check_active():
                    return None
            case Phase.CHOOSE_OUT_OF_ORDER_PRESIDENT:
                if player_index != current_state.current_president:
                    return None
                if not current_state.is_choose_out_of_order_president_active():
                    return None
            case Phase.KILL:
                if player_index != current_state.current_president:
                    return None
                if not current_state.is_kill_active():
                    return None
            case Phase.GAME_ENDED:
                return None
            case _:
                assert False

        print(f"Asking player {player_index} phase {current_state.phase}")
        player_state = self.hide_from_player(
            source_state=current_state,
            player_index=player_index,
            player_role=current_state.roles[player_index],
        )

        player = self.players[player_index]
        return player.action(state=player_state)
