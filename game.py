from board import Board
from placements import Placements
import random
from collections import deque  # очередь для алгоритма добивания


class Game:
    def __init__(self):
        self.player_board = Board()  # Доска игрока
        self.computer_board = Board() # Доска компьютера
        self.move_stack = [] # Стэк ходов
        self.current_turn = 'player'  # Чей ход
        self.move_number = 0 # Номер хода

        # Очередь клеток для добивания корабля
        self.target_queue = deque()

        # Доп функция: бомба, бьёт по квадрату 2 на 2, дается 2 штуки за игру
        self.bombs_left = 2

    """ Автоматическая расстановка всех кораблей. 20 попыток случайной расстановки, потом готовый вариант """
    def _auto_place_all_ships(self, board, board_name="Доска"):
        print(f"\n{board_name}: автоматическая расстановка кораблей...")
        for attempt in range(20):
            self._clear_board(board)
            ships = []
            for length, count in board.SHIPS.items():
                for _ in range(count):
                    ships.append(length)
            random.shuffle(ships)
            success = True
            for length in ships:
                placed = False
                for _ in range(500):
                    row = random.randint(1, 10)
                    col = random.randint(1, 10)
                    orientation = random.choice(['h', 'v'])
                    ok, _ = board.add_ship(row, col, length, orientation)
                    if ok:
                        placed = True
                        break
                if not placed:
                    success = False
                    break
            if success and len(board.ships_placed) == 10:
                print(f"Рандомная расстановка удалась! (попытка {attempt + 1})")
                if board_name == "ПОЛЕ КОМПЬЮТЕРА":
                    print("  (корабли скрыты)")
                else:
                    board.display(hide_ships=False)
                return
        print("  Использую готовый проверенный вариант...")
        self._use_predefined_placement(board)
        if board_name == "ПОЛЕ КОМПЬЮТЕРА":
            print("  (корабли скрыты)")
        else:
            board.display(hide_ships=False)

    """Использует готовый проверенный вариант расстановки."""
    def _use_predefined_placement(self, board):
        self._clear_board(board)
        placement = Placements.get_random_placement()
        for row, col, orientation, length in placement:
            ok, _ = board.add_ship(row, col, length, orientation)
            if not ok:
                self._use_predefined_placement(board)
                return
        print(f"   Готовый вариант применён (всего {len(board.ships_placed)} кораблей)")

    """Полностью очищает доску."""
    def _clear_board(self, board):
        for r in range(10):
            for c in range(10):
                board.grid[r][c] = 0
        board.ships_placed.clear()
        board.ships_to_place = board.SHIPS.copy()
        board._next_ship_id = 1

    """Ручная расстановка кораблей игроком."""
    def _place_ships_manual(self, board, board_name):
        print(f"\n{'='*60}")
        print(f"РАССТАНОВКА КОРАБЛЕЙ: {board_name}")
        print(f"{'='*60}")
        print("\nПРАВИЛА:")
        print("   Корабли не должны соприкасаться даже углами")
        print("   Координаты: от 1 до 10")
        print("   Формат: строка столбец h/v длина")
        print("   Пример: 3 5 h 4")
        print("   'auto' - автоматическая расстановка")
        print("   'clear' - очистить поле и начать заново")

        ships_left = board.ships_to_place.copy()
        while any(count > 0 for count in ships_left.values()):
            print(f"\n{'─'*50}")
            print("ОСТАЛОСЬ РАЗМЕСТИТЬ:")
            for length, count in ships_left.items():
                if count > 0:
                    print(f"   {length}-палубный: {count} шт.")
            print(f"\nТЕКУЩЕЕ ПОЛЕ:")
            board.display(hide_ships=False)
            user_input = input("\n-> ").strip().lower()
            if user_input == 'auto':
                self._auto_place_all_ships(board, board_name)
                ships_left = board.ships_to_place.copy()
                continue
            if user_input == 'clear':
                self._clear_board(board)
                ships_left = board.ships_to_place.copy()
                print(" Поле очищено")
                continue
            try:
                parts = user_input.split()
                if len(parts) != 4:
                    print("Формат: строка столбец h/v длина")
                    continue
                row = int(parts[0])
                col = int(parts[1])
                orient = parts[2]
                length = int(parts[3])
                if not (1 <= row <= 10 and 1 <= col <= 10):
                    print("Координаты от 1 до 10")
                    continue
                if orient not in ('h', 'v'):
                    print("Ориентация 'h' или 'v'")
                    continue
                if length not in ships_left or ships_left[length] <= 0:
                    print(f"Кораблей длины {length} больше не нужно")
                    continue
                success, msg = board.add_ship(row, col, length, orient)
                print(f"  {msg}")
                if success:
                    ships_left = board.ships_to_place.copy()
            except ValueError:
                print("Введите числа")
            except Exception as e:
                print(f"{e}")
        print(f"\n{'='*60}")
        print(" РАССТАНОВКА ЗАВЕРШЕНА!")
        board.display(hide_ships=False)
        input("\nНажмите Enter...")

   # Ход компьютера: если в очереди есть клетки для добивания — стреляем по ним, в другом случае стреляем в случайную ещё не обстрелянную клетку, после попадания соседние клетки кладём в очередь.
    def _computer_shot(self):
        while self.target_queue:
            ext_r, ext_c = self.target_queue.popleft()
            if self.player_board.grid[ext_r - 1][ext_c - 1] < 0:
                continue
            return self._do_computer_shot(ext_r, ext_c, dobivanie=True)

        unchecked = []
        for r in range(10):
            for c in range(10):
                if self.player_board.grid[r][c] >= 0:
                    unchecked.append((r + 1, c + 1))
        if unchecked:
            ext_r, ext_c = random.choice(unchecked)
            return self._do_computer_shot(ext_r, ext_c, dobivanie=False)
        return 'miss'

    # Выполняет один выстрел компьютера и обновляет очередь добивания
    def _do_computer_shot(self, ext_r, ext_c, dobivanie):
        before_cell = self.player_board.grid[ext_r - 1][ext_c - 1]
        result = self.player_board.shoot(ext_r, ext_c)
        self._add_to_stack(ext_r, ext_c, 'computer', result, before_cell)
        if result == 'hit':
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = ext_r + dr, ext_c + dc
                if 1 <= nr <= 10 and 1 <= nc <= 10:
                    if self.player_board.grid[nr - 1][nc - 1] >= 0:
                        self.target_queue.append((nr, nc))
        elif result == 'kill':
            self.target_queue.clear()
        tag = " (добивание)" if dobivanie else ""
        print(f"Компьютер -> ({ext_r}, {ext_c}) -> {self._result_to_text(result)}{tag}")
        return result

    # Ход игрока
    def _player_shot(self, row, col):
        before_cell = self.computer_board.grid[row - 1][col - 1]
        result = self.computer_board.shoot(row, col)
        self._add_to_stack(row, col, 'player', result, before_cell)
        print(f"\nВы → ({row}, {col}) → {self._result_to_text(result)}")
        return result

    """
    Дополнительная функция: бомба
    Бьёт по квадрату 2x2: клетка (row, col) — левый верхний угол.
    Возвращает True, если бомба сброшена (тратит ход), иначе False.
    """
    def _bomb_shot(self, row, col):
        if self.bombs_left <= 0:
            print("Бомбы закончились!")
            return False
        if not (1 <= row <= 9 and 1 <= col <= 9):
            print("Бомба не влезает! Левый верхний угол должен быть от 1 до 9.")
            return False
        cells = [(row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1)]
        print(f"\n💣 БОМБА по квадрату 2x2 от ({row}, {col}):")
        hits = 0
        for (r, c) in cells:
            before = self.computer_board.grid[r - 1][c - 1]
            result = self.computer_board.shoot(r, c)
            self._add_to_stack(r, c, 'player', result, before)
            if result in ('hit', 'kill'):
                hits += 1
            print(f"   ({r}, {c}) → {self._result_to_text(result)}")
        self.bombs_left -= 1
        print(f"Попаданий: {hits}. Осталось бомб: {self.bombs_left}")
        return True

    def _result_to_text(self, result):
        if result == 'miss':
            return "МИМО!"
        elif result == 'hit':
            return "РАНЕН!"
        elif result == 'kill':
            return "УБИТ!"
        return result

    # Возвращает доску, по которой стрелял игрок
    def _get_target_board(self, player):
        if player == 'player':
            return self.computer_board
        return self.player_board

    # Добавляет ход в стек истории
    def _add_to_stack(self, row, col, player, result, before_cell):
        self.move_number += 1
        self.move_stack.append({
            'move_num': self.move_number,
            'player': player,
            'row': row,
            'col': col,
            'result': result,
            'before_cell': before_cell,
        })

    # Показывает последние ходы из стека
    def show_move_history(self):
        if not self.move_stack:
            print("История ходов пустая")
            return
        print("\n ПОСЛЕДНИЕ ХОДЫ:")
        for move in self.move_stack[-10:]:
            who = "Вы" if move['player'] == 'player' else "Компьютер"
            print(f"  {move['move_num']}. {who} → ({move['row']}, {move['col']}) - {move['result']}")

    # Отменяет последний ход и восстанавливает состояние клетки
    def undo_last_move(self):
        if not self.move_stack:
            print("Нет ходов для отмены")
            return False
        move = self.move_stack.pop()
        board = self._get_target_board(move['player'])
        row = move['row'] - 1
        col = move['col'] - 1
        board.grid[row][col] = move['before_cell']
        self.move_number = self.move_stack[-1]['move_num'] if self.move_stack else 0
        self.current_turn = move['player']
        who = "ваш ход" if move['player'] == 'player' else "ход компьютера"
        print(f"Отменён ход №{move['move_num']}: ({move['row']}, {move['col']}) — {move['result']}. Теперь снова {who}.")
        return True

    def _display_both_boards(self):
        print("\n" + "=" * 86)
        print("ВАШЕ ПОЛЕ".ljust(50) + "ПОЛЕ ПРОТИВНИКА")
        print("=" * 86)
        player_lines = self.player_board.get_display_string(hide_ships=False).split('\n')
        computer_lines = self.computer_board.get_display_string(hide_ships=True).split('\n')
        max_lines = max(len(player_lines), len(computer_lines))
        for i in range(max_lines):
            left = player_lines[i] if i < len(player_lines) else " " * 37
            right = computer_lines[i] if i < len(computer_lines) else " " * 37
            print(f"{left:<41}    {right}")
        player_ships = self.player_board.get_ships_count()
        computer_ships = self.computer_board.get_ships_count()
        print("\nСТАТИСТИКА:")
        print(f"  Ваши корабли: {sum(player_ships.values())} шт.")
        print(f"  Корабли врага: {sum(computer_ships.values())} шт.")
        print(f"  Бомбы: {self.bombs_left} шт.")

    def run(self):
        print("\n" + "="*60)
        print("МОРСКОЙ БОЙ")
        print("="*60)
        self._place_ships_manual(self.player_board, "ВАШЕ ПОЛЕ")
        self._auto_place_all_ships(self.computer_board, "ПОЛЕ КОМПЬЮТЕРА")
        print("\n" + "="*60)
        print("ИГРА НАЧАЛАСЬ!")
        print("="*60)

        while True:
            self._display_both_boards()

            if self.current_turn == 'player':
                print(f"\nВАШ ХОД! (№{self.move_number + 1})")
                print("Обычный выстрел: строка столбец (пример: 3 5)")
                print(f"Бомба 2x2: bomb строка столбец (осталось {self.bombs_left})")
                print("Команды: 'undo' - отменить, 'history' - история, 'exit' - выход")

                user_input = input("\n➜ ").strip().lower()

                if user_input == 'exit':
                    print("\nДо свидания!")
                    break
                if user_input == 'undo':
                    self.undo_last_move()
                    continue
                if user_input == 'history':
                    self.show_move_history()
                    continue

                parts = user_input.split()

                # Бомба
                if parts and parts[0] == 'bomb':
                    try:
                        if len(parts) != 3:
                            print("Формат бомбы: bomb строка столбец (пример: bomb 4 5)")
                            continue
                        row = int(parts[1])
                        col = int(parts[2])
                    except ValueError:
                        print("Введите числа")
                        continue
                    used = self._bomb_shot(row, col)
                    if not used:
                        continue
                    if self.computer_board.all_ships_sunk():
                        self._display_both_boards()
                        print("ПОЗДРАВЛЯЮ! ВЫ ПОБЕДИЛИ!")
                        break
                    self.current_turn = 'computer'
                    continue

                # Обычный выстрел
                try:
                    if len(parts) != 2:
                        print("Введите два числа от 1 до 10")
                        continue
                    row = int(parts[0])
                    col = int(parts[1])
                    if not (1 <= row <= 10 and 1 <= col <= 10):
                        print("Координаты от 1 до 10")
                        continue
                    r_in, c_in = row - 1, col - 1
                    if self.computer_board.grid[r_in][c_in] < 0:
                        print("Сюда уже стреляли!")
                        continue
                    result = self._player_shot(row, col)
                    if result == 'already':
                        print("Сюда уже стреляли. Выберите другую клетку.")
                        continue
                    if self.computer_board.all_ships_sunk():
                        self._display_both_boards()
                        print("ПОЗДРАВЛЯЮ! ВЫ ПОБЕДИЛИ!")
                        break
                    if result in ('hit', 'kill'):
                        self.current_turn = 'player'
                    else:
                        self.current_turn = 'computer'
                except ValueError:
                    print("Введите числа")
                except Exception as e:
                    print(f" {e}")

            else:
                print(f"\n ХОД КОМПЬЮТЕРА...")
                user_input = input("Нажмите Enter, 'undo' - отменить последний ход, 'history' - история... ").strip().lower()
                if user_input == 'undo':
                    self.undo_last_move()
                    continue
                if user_input == 'history':
                    self.show_move_history()
                    continue
                result = self._computer_shot()
                if self.player_board.all_ships_sunk():
                    self._display_both_boards()
                    print("\n" + "💀"*30)
                    print("ВСЕ ВАШИ КОРАБЛИ УНИЧТОЖЕНЫ! ВЫ ПРОИГРАЛИ!")
                    print("💀"*30)
                    break
                if result in ('hit', 'kill'):
                    self.current_turn = 'computer'
                else:
                    self.current_turn = 'player'

        print("\n" + "="*60)
        print("ИТОГИ ИГРЫ")
        print("="*60)
        print(f"Всего ходов: {self.move_number}")
