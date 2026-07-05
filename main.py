from engine.controller import Controller
from engine.player import DummyPlayer


def main():
    player_names = ["Alice", "Bob", "Charlie", "Danny", "Elizabeth", "Frank", "George", "Hillary", "Iris", "John"]
    players = [DummyPlayer(name=name) for name in player_names]

    while True:
        for player_count in [5, 6, 7, 8, 9, 10]:
            controller = Controller(players=players[:player_count])
            controller.run_game()


if __name__ == '__main__':
    main()
