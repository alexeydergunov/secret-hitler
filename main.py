from engine.controller import Controller
from engine.player import DummyPlayer


def main():
    player_names = ["Alice", "Bob", "Charlie", "Danny", "Elizabeth", "Frank", "George"]
    players = [DummyPlayer(name=name) for name in player_names]

    controller = Controller(players=players)
    controller.run_game()


if __name__ == '__main__':
    main()
