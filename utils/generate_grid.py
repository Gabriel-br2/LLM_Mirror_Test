import random

import numpy as np


def _generate_grid(y_grid_max, x_grid_max, characters_num, door_size=3):
    """
    Generates a 2D grid with borders, randomly placed characters, and a door on a random border.

    Args:
        y_grid_max (int): Number of rows in the grid.
        x_grid_max (int): Number of columns in the grid.
        characters_num (int): Number of characters to place inside the grid.

    Returns:
        tuple:
            - mainGrid (np.ndarray): The generated grid as a 2D numpy array of strings.
            - positions (list of tuple): List of (x, y) positions where characters were placed.
    """
    # Initialize the grid filled with '.'
    mainGrid = np.full((y_grid_max, x_grid_max), ".", dtype=str)

    # Add borders to the grid (set border cells to '#')
    mainGrid[0, :] = "#"
    mainGrid[-1, :] = "#"
    mainGrid[:, 0] = "#"
    mainGrid[:, -1] = "#"

    # Add characters to the grid at random positions (not on the border)
    positions = set()
    while len(positions) < characters_num:
        x = random.randint(1, x_grid_max - 2)  # Avoid border columns
        y = random.randint(1, y_grid_max - 2)  # Avoid border rows
        positions.add((x, y))

    positions = list(positions)

    # Place each character in the grid, using its index as the label
    for idx, (x, y) in enumerate(positions, start=1):
        mainGrid[x, y] = str(idx)

    # Add a door ('D') on a random border
    # door_wall: 0=North, 1=East, 2=South, 3=West
    door_wall = random.choice([0, 1, 2, 3])
    wall_range = (
        range(1, x_grid_max - 1) if door_wall in [0, 2] else range(1, y_grid_max - 1)
    )

    door_size_mid = (door_size - 1) // 2

    if door_wall in [0, 2]:  # Norte ou Sul
        door_x = random.choice(wall_range)
        door_y = 0 if door_wall == 0 else y_grid_max - 1
        d1, d2 = door_x - door_size_mid, door_x + door_size_mid + 1

        d1 = max(d1+1, 0)
        d2 = min(d2, x_grid_max-1)
        mainGrid[door_y, d1:d2] = "D"

    elif door_wall in [1, 3]:  # Leste ou Oeste
        door_x = x_grid_max - 1 if door_wall == 1 else 0
        door_y = random.choice(wall_range)
        d1, d2 = door_y - door_size_mid, door_y + door_size_mid + 1
        
        d1 = max(d1+1, 0)
        d2 = min(d2, x_grid_max-1)
        mainGrid[d1:d2, door_x] = "D"

    return mainGrid, positions
