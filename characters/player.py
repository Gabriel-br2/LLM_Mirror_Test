from characters.character import Character

class Player(Character):
    ACTION_MAP = {
        "move_left":  (0, -1),
        "move_right": (0, 1),
        "move_up":    (-1, 0),
        "move_down":  (1, 0),
    }

    def __init__(self, *args):
        super().__init__(*args)

    def get_move(self, action: str) -> tuple[int, int] | None:
        if action not in self.ACTION_MAP:
            return None

        dy, dx = self.ACTION_MAP[action]
        y, x = self.pos
        return (y + dy, x + dx)
