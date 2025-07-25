import pygame

# Initialize font system when module is imported
pygame.font.init()


class Character:
    """
    Base Character class for all game characters (players and NPCs).
    Handles position, drawing, and movement logic.
    """

    def __init__(self, idx, pos, color, ball_radius, square_tam, door_state):
        """
        Initializes a Character instance.

        Args:
            idx (int): Character index or identifier.
            pos (tuple): Initial position (y, x) of the character on the grid.
            color (tuple): RGB color tuple for drawing the character.
            ball_radius (int): Radius of the character's circle representation.
            square_tam (int): Size of each grid square (for drawing).
        """
        self.idx = idx
        self.pos = pos
        self.color = color
        self.ball_radius = ball_radius
        self.square_tam = square_tam
        self.door_state = door_state

    def can_move(self, grid, new_pos):
        """
        Checks if the character can move to the specified position.

        Args:
            grid (2D array-like): The current game grid.
            new_pos (tuple): The target position (y, x).

        Returns:
            bool: True if the move is valid (cell is empty), False otherwise.
        """
        y, x = new_pos
        return grid[y, x] == "." or (grid[y, x] == "D" and self.door_state == "open") 

    def move(self, grid, new_pos, door_state):
        """
        Moves the character to a new position if the move is valid.

        Args:
            grid (2D array-like): The current game grid.
            new_pos (tuple): The target position (y, x).

        Returns:
            bool: True if the move was successful, False otherwise.
        """
        self.door_state = door_state
        if self.can_move(grid, new_pos):
            grid[self.pos] = "."  # Clear current position
            self.pos = new_pos
            grid[new_pos[0], new_pos[1]] = str(self.idx)  # Mark new position
            return True
        return False

    def draw(self, screen):
        """
        Draws the character as a circle on the given Pygame screen.

        Args:
            screen (pygame.Surface): The Pygame surface to draw on.
        """
        x, y = self.pos[1], self.pos[0]
        center = (
            x * self.square_tam + self.square_tam // 2,
            y * self.square_tam + self.square_tam // 2,
        )
        pygame.draw.circle(screen, self.color, center, self.ball_radius)
        
        # Draw the character ID number in the center with contrasting color
        font = pygame.font.Font(None, 24)
        id_text = str(self.idx)
        
        # Choose text color based on background color for better contrast
        # Calculate brightness of the character color
        r, g, b = self.color
        brightness = (r * 0.299 + g * 0.587 + b * 0.114)
        
        # Use white text on dark colors, black text on light colors
        text_color = (255, 255, 255) if brightness < 128 else (0, 0, 0)
        
        text_surface = font.render(id_text, True, text_color)
        text_rect = text_surface.get_rect(center=center)
        screen.blit(text_surface, text_rect)
