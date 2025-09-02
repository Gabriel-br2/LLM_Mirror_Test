import random
from characters.character import Character


class NPC(Character):
    def get_random_move(self, grid) -> tuple[int, int]:
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        random.shuffle(directions)

        for dy, dx in directions:
            new_y, new_x = self.pos[0] + dy, self.pos[1] + dx
            if self.can_move(grid, (new_y, new_x)):
                return (new_y, new_x)

        return self.pos
