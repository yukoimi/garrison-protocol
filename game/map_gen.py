"""卫戍协议 - 随机地图生成"""
import random
from enum import Enum
from dataclasses import dataclass


class CellType(Enum):
    PATH = 0
    RANGED = 1
    WALL = 2


@dataclass
class MapCell:
    x: int
    y: int
    cell_type: CellType = CellType.WALL
    occupied: bool = False
    operator_id: str = ""


class GameMap:
    def __init__(self, cols: int = 14, rows: int = 7):
        self.cols = cols; self.rows = rows
        self.cells: list[list[MapCell]] = []
        self.path_cells: list[tuple[int, int]] = []

    def generate(self, seed=None):
        if seed is not None: random.seed(seed)
        self.cells = [[MapCell(x, y) for y in range(self.rows)] for x in range(self.cols)]
        self.path_cells = []

        entry_y = random.randint(1, self.rows - 2)
        exit_y = random.randint(1, self.rows - 2)
        path = self._gen_path(entry_y, exit_y)

        for cx, cy in path:
            if 0 <= cx < self.cols and 0 <= cy < self.rows:
                self.cells[cx][cy].cell_type = CellType.PATH
                self.path_cells.append((cx, cy))

        for cx, cy in path:
            for dy in [-1, 1]:
                ny = cy + dy
                if 0 <= ny < self.rows:
                    cell = self.cells[cx][ny]
                    if cell.cell_type == CellType.WALL:
                        cell.cell_type = CellType.RANGED

        for cx, cy in path:
            for dy in [-2, 2]:
                ny = cy + dy
                if 0 <= ny < self.rows and random.random() < 0.6:
                    cell = self.cells[cx][ny]
                    if cell.cell_type == CellType.WALL:
                        cell.cell_type = CellType.RANGED

        for x in range(self.cols):
            for y in [0, self.rows - 1]:
                cell = self.cells[x][y]
                if cell.cell_type == CellType.WALL:
                    cell.cell_type = CellType.RANGED
        return self

    def _gen_path(self, start_y: int, end_y: int) -> list[tuple[int, int]]:
        """确保4连通: 上下移动时插入中间格子形成L形"""
        path = []
        cx = self.cols - 1; cy = start_y; path.append((cx, cy))
        while cx > 0:
            old_cy = cy
            if cx > self.cols // 3:
                if random.random() < 0.2 and 1 <= cy < self.rows - 2:
                    cy += random.choice([-1, 1])
            else:
                if cy < end_y and cy < self.rows - 2: cy += 1
                elif cy > end_y and cy > 1: cy -= 1
                elif random.random() < 0.1: cy += random.choice([-1, 1])
            cy = max(1, min(self.rows - 2, cy))
            # 如果上下移动了, 先插入同列的中间点(消除对角)
            if cy != old_cy:
                path.append((cx, cy))  # L形拐点
            cx -= 1
            path.append((cx, cy))
        return path

    def get_cell(self, x: int, y: int) -> MapCell | None:
        if 0 <= x < self.cols and 0 <= y < self.rows: return self.cells[x][y]
        return None

    def can_deploy(self, x: int, y: int, is_melee: bool) -> bool:
        cell = self.get_cell(x, y)
        if not cell or cell.occupied: return False
        if cell.cell_type == CellType.WALL: return False
        if is_melee and cell.cell_type != CellType.PATH: return False
        if not is_melee and cell.cell_type != CellType.RANGED: return False
        return True
