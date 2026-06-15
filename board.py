class Board:
    
    SIZE = 10
    SHIPS = {4: 1, 3: 2, 2: 3, 1: 4}

    def __init__(self):
        self.grid = [[0 for _ in range(self.SIZE)] for _ in range(self.SIZE)]
        # Сколько кораблей ещё нужно поставить
        self.ships_to_place = self.SHIPS.copy()
        # Уже поставленные корабли: [id, длина, список_координат]
        self.ships_placed = []
        # Следующий уникальный ID корабля
        self._next_ship_id = 1

    def _to_internal(self, row, col):
        """Преобразует координаты игрока 1..10 во внутренние координаты 0...9"""
        if 1 <= row <= self.SIZE and 1 <= col <= self.SIZE:
            return row - 1, col - 1
        return None

    def _to_external(self, row, col):
        """Преобразует внутренние координаты 0..9 во внешние координаты 1...10"""
        return row + 1, col + 1

    def _get_neighbors(self, row, col):
        """Возвращает соседние клетки, включая диагонали"""
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if 0 <= r < self.SIZE and 0 <= c < self.SIZE:
                    neighbors.append((r, c))
        return neighbors

    def _has_adjacent_ships(self, cells):
        """Проверяет, есть ли рядом с указанными клетками корабли"""
        for row, col in cells:
            for nr, nc in self._get_neighbors(row, col):
                if self.grid[nr][nc] > 0:
                    return True
        return False

    def _is_valid_position(self, cells):
        """
        Проверяет, можно ли разместить корабль в указанных клетках.
        Условия:
        1. Все клетки внутри поля
        2. Все клетки свободны
        3. Нет соседних кораблей даже по диагонали
        """
        for row, col in cells:
            if not (0 <= row < self.SIZE and 0 <= col < self.SIZE):
                return False
            if self.grid[row][col] != 0:
                return False
        if self._has_adjacent_ships(cells):
            return False
        return True

    def _get_ship_by_cell(self, row, col):
        """Находит корабль, которому принадлежит клетка"""
        cell = self.grid[row][col]
        if cell == 0 or cell == -99:
            return None
        ship_id = abs(cell)
        for ship in self.ships_placed:
            if ship[0] == ship_id:
                return ship[2]
        return None

    def _is_ship_sunk(self, ship_cells):
        """Проверяет, уничтожен ли корабль"""
        if not ship_cells:
            return False
        for row, col in ship_cells:
            if self.grid[row][col] > 0:
                return False
        return True

    def add_ship(self, start_row, start_col, length, orientation):
        """Добавляет корабль на доску"""
        if orientation not in ('h', 'v'):
            return False,
        if length not in self.SHIPS:
            return False, "Такой длины корабля нет в стандартном наборе"
        if self.ships_to_place.get(length, 0) <= 0:
            return False, f"Кораблей длиной {length} больше не нужно"
        internal = self._to_internal(start_row, start_col)
        if internal is None:
            return False, f"Координаты должны быть от 1 до {self.SIZE}"
        r, c = internal
        cells = []
        for i in range(length):
            if orientation == 'h':
                new_r, new_c = r, c + i
            else:
                new_r, new_c = r + i, c
            if not (0 <= new_r < self.SIZE and 0 <= new_c < self.SIZE):
                return False, "Корабль выходит за границы поля"
            cells.append((new_r, new_c))
        if not self._is_valid_position(cells):
            return False, "Клетки заняты или корабли соприкасаются"
        ship_id = self._next_ship_id
        self._next_ship_id += 1
        for row, col in cells:
            self.grid[row][col] = ship_id
        self.ships_placed.append([ship_id, length, cells])
        self.ships_to_place[length] -= 1
        return True, f"Корабль длиной {length} размещён"

    def remove_ship(self, ship_cells):
        if not ship_cells:
            return False
        first_row, first_col = ship_cells[0]
        cell = self.grid[first_row][first_col]
        if cell == 0 or cell == -99:
            return False
        ship_id = abs(cell)
        for i, ship in enumerate(self.ships_placed):
            if ship[0] == ship_id:
                length = ship[1]
                for row, col in ship[2]:
                    self.grid[row][col] = 0
                del self.ships_placed[i]
                self.ships_to_place[length] = self.ships_to_place.get(length, 0) + 1
                return True
        return False

    def shoot(self, row, col):
        """
        'invalid' координаты вне поля
        'already' сюда уже стреляли
        'miss' мимо
        'hit' ранен
        'kill' убит
        """
        internal = self._to_internal(row, col)
        if internal is None:
            return 'invalid'
        r, c = internal
        cell = self.grid[r][c]
        if cell == 0:
            self.grid[r][c] = -99
            return 'miss'
        if cell < 0:
            return 'already'
        ship_cells = self._get_ship_by_cell(r, c)
        self.grid[r][c] = -cell
        if self._is_ship_sunk(ship_cells):
            return 'kill'
        return 'hit'

    def all_ships_sunk(self):
        """Проверяет, уничтожены ли все корабли"""
        for row in range(self.SIZE):
            for col in range(self.SIZE):
                if self.grid[row][col] > 0:
                    return False
        return True

    def get_ships_count(self):
        """Возвращает количество оставшихся кораблей по длинам"""
        ships_left = {}
        for ship in self.ships_placed:
            if not self._is_ship_sunk(ship[2]):
                length = ship[1]
                ships_left[length] = ships_left.get(length, 0) + 1
        return ships_left

    def _cell_to_symbol(self, cell, hide_ships=False):
        """Преобразует значение клетки в символ для вывода"""
        if hide_ships and cell > 0:
            return "·"
        if cell == 0:
            return "·" 
        if cell == -99:
            return "○"
        if cell < 0:
            return "✗"
        return "■"

    def display(self, hide_ships=False):
        print("   ", end="")
        for c in range(1, self.SIZE + 1):
            print(f"{c:2}", end=" ")
        print()
        print("   +" + "---" * self.SIZE + "+")
        for r in range(self.SIZE):
            print(f"{r + 1:2} |", end=" ")
            for c in range(self.SIZE):
                cell = self.grid[r][c]
                print(self._cell_to_symbol(cell, hide_ships), end="  ")
            print("|")
        print("   +" + "---" * self.SIZE + "+")

    def get_display_string(self, hide_ships=False):
        """Возвращает строковое представление доски для вывода двух досок рядом"""
        lines = []
        header = "    " + " ".join(f"{c:2}" for c in range(1, self.SIZE + 1))
        border = "   +" + "---" * self.SIZE + "+"
        lines.append(header)
        lines.append(border)

        for r in range(self.SIZE):
            symbols = []
            for c in range(self.SIZE):
                symbol = self._cell_to_symbol(self.grid[r][c], hide_ships)
                symbols.append(f"{symbol:2}")
            lines.append(f"{r + 1:2} |" + " ".join(symbols) + "|")
        lines.append(border)
        return "\n".join(lines)
