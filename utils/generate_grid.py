import random
import numpy as np


def _generate_grid(height, width, num_characters, door_size=3):
    def add_borders(grid: np.ndarray) -> None:
        grid[0, :] = "#"
        grid[-1, :] = "#"
        grid[:, 0] = "#"
        grid[:, -1] = "#"

    def generate_character_positions() -> list[tuple[int, int]]:
        positions = set()
        while len(positions) < num_characters:
            x = random.randint(1, width - 2)
            y = random.randint(1, height - 2)
            positions.add((x, y))
        return list(positions)

    def place_characters(grid: np.ndarray, positions: list[tuple[int, int]]) -> None:
        for idx, (x, y) in enumerate(positions):
            grid[y, x] = str(idx)

    def add_door(grid: np.ndarray) -> None:
        wall = random.choice([0, 1, 2, 3])
        half_size = (door_size - 1) // 2

        if wall in [0, 2]:
            x = random.randint(1, width - 2)
            y = 0 if wall == 0 else height - 1
            start, end = x - half_size, x + half_size + 1
            start = max(start + 1, 0)
            end = min(end, width - 1)
            grid[y, start:end] = "D"

        else:
            x = width - 1 if wall == 1 else 0
            y = random.randint(1, height - 2)
            start, end = y - half_size, y + half_size + 1
            start = max(start + 1, 0)
            end = min(end, height - 1)
            grid[start:end, x] = "D"

    grid = np.full((height, width), ".", dtype=str)

    add_borders(grid)
    positions = generate_character_positions()
    place_characters(grid, positions)
    add_door(grid)

    return grid, positions
