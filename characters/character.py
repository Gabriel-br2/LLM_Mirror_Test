import pygame
pygame.font.init()

class Character:
    def __init__(self, idx, pos, color, radius, cell_size, door_state="closed"):
        self.idx = idx
        self.pos = pos
        self.color = color
        self.radius = radius
        self.cell_size = cell_size
        self.door_state = door_state

        self.font = pygame.font.Font(None, 24)

    def can_move(self, grid, new_pos):
        y, x = new_pos
        return grid[y, x] == "." or (grid[y, x] == "D" and self.door_state == "open") 

    def _get_text_color(self) -> tuple[int, int, int]:
        r, g, b = self.color
        brightness = r * 0.299 + g * 0.587 + b * 0.114
        return (255, 255, 255) if brightness < 128 else (0, 0, 0)

    def _grid_is_free(self, grid, pos) -> bool:
        y, x = pos
        cell = grid[y, x]
        return cell == "." or (cell == "D" and self.door_state == "open")

    def move(self, grid, new_pos, door_state: str) -> bool:
        self.door_state = door_state
        if self._grid_is_free(grid, new_pos):
            y, x = self.pos
            grid[y, x] = "."  
            self.pos = new_pos
            grid[new_pos[0], new_pos[1]] = str(self.idx) 
            return True
        return False

    def draw(self, screen: pygame.Surface) -> None:
        y, x = self.pos
        center = (
            x * self.cell_size + self.cell_size // 2,
            y * self.cell_size + self.cell_size // 2,
        )

        pygame.draw.circle(screen, self.color, center, self.radius)

        text_surface = self.font.render(str(self.idx), True, self._get_text_color())
        text_rect = text_surface.get_rect(center=center)
        screen.blit(text_surface, text_rect)
