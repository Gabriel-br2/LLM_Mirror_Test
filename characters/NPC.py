import random

from characters.character import Character


class NPC(Character):
    """
    NPC (Non-Player Character) class that inherits from Character.
    Provides random movement logic for the NPC within the grid.
    """

    def get_random_move(self, grid):
        """
        Determines a random valid move for the NPC.

        Args:
            grid (2D array-like): The current game grid.

        Returns:
            tuple: The new position (y, x) if a valid move is found,
                   otherwise returns the current position.
        """
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
        random.shuffle(directions)  # Shuffle directions for randomness
        for dy, dx in directions:
            new_y, new_x = self.pos[0] + dy, self.pos[1] + dx
            if self.can_move(grid, (new_y, new_x)):
                return (new_y, new_x)  # Return the first valid move found
        return self.pos  # If no valid move, stay in
