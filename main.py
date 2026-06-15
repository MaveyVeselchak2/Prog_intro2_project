"""Главный модуль для запуска игры Морской бой"""
from game import Game


class Main:
    @staticmethod
    def run():
        while True:
            print("""
        ╔════════════════════════════════════════╗
        ║        МОРСКОЙ БОЙ - BATTLE SHIP       ║
        ║         Игра против компьютера         ║
        ╚════════════════════════════════════════╝
            """)
            game = Game()
            game.run()
            again = input("\nСыграть ещё? (y/n): ").strip().lower()
            if again not in ('y', 'yes', 'да'):
                print("\n Спасибо за игру!")
                break


if __name__ == "__main__":
    Main.run()
