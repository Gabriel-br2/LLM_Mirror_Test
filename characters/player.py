import pygame

from characters.character import Character


class Player(Character):
    """
    Player class that inherits from Character.
    Handles player movement based on keyboard input events.
    """

    def get_move(self, event):
        """
        Determines the new position of the player based on the keyboard event.

        Args:
            event (pygame.event.Event): The keyboard event containing the key pressed.

        Returns:
            tuple: The new position (y, x) if a valid key is pressed,
                   otherwise returns the current position.
        """
        moves = {
            pygame.K_1: (self.pos[0], self.pos[1] - 1),  # Move left
            pygame.K_2: (self.pos[0], self.pos[1] + 1),  # Move right
            pygame.K_3: (self.pos[0] - 1, self.pos[1]),  # Move up
            pygame.K_4: (self.pos[0] + 1, self.pos[1]),  # Move down
        }
        return moves.get(event.key, self.pos)
