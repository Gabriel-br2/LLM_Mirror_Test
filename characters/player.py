

from characters.character import Character

class Player(Character):
    """
    Player class that inherits from Character.
    Handles self movement based on keyboard input events.
    """
    def __init__(self, *args):
        super().__init__(*args)

    def get_move(self, action):
        """
        Determines the new position of the player based on the keyboard event.

        Args:
            action (str): The keyboard event containing the key pressed.

        Returns:
            tuple: The new position (y, x) if a valid key is pressed,
                   otherwise returns the current position.
        """

        if action == "move_left":
            new_pos = (self.pos[0], self.pos[1] - 1)

        elif action == "move_right":
            new_pos = (self.pos[0], self.pos[1] + 1)

        elif action == "move_up":
            new_pos = (self.pos[0] - 1, self.pos[1])

        elif action == "move_down":
            new_pos = (self.pos[0] + 1, self.pos[1])

        else:
            new_pos = None

        return new_pos
