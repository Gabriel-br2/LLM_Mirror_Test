import json
import random

import pygame

from characters.NPC import NPC
from characters.player import Player
from utils.config import mainConfig
from utils.generate_grid import _generate_grid

# Load configuration from YAML file
cfg = mainConfig()
cfg.read_config()


class Simulation:
    """
    Main Simulation class for the grid-based game.
    Handles initialization, main loop, event handling, rendering, and game logic.
    """

    COLORS = {
        1: (255, 0, 0),  # Red
        2: (0, 255, 0),  # Green
        3: (0, 0, 255),  # Blue
        4: (255, 255, 0),  # Yellow
        5: (255, 165, 0),  # Orange
        6: (128, 0, 128),  # Purple
        7: (0, 255, 255),  # Cyan
        8: (255, 192, 203),  # Pink
        9: (255, 140, 0),  # Dark Orange
    }

    def __init__(self):
        """
        Initializes the simulation, loads configuration, creates grid and characters,
        and sets up Pygame.
        """
        self.turn = 0  # Current turn number
        self.memory = []  # Stores actions and thoughts for each turn
        self.door_state = "closed"  # Door can be "open" or "closed"

        self._load_config()  # Load configuration values
        self._init_grid_and_characters()  # Create grid and characters
        self._init_pygame()  # Initialize Pygame window and clock

        # self._print_ascii_grid()  # Uncomment to print grid in ASCII

    def _load_config(self):
        """
        Loads configuration values from the config file and sets simulation parameters.
        """
        # Add 2 to grid size for borders
        self.x_grid_max = cfg.config["screen"]["x_grid_max"] + 2
        self.y_grid_max = cfg.config["screen"]["y_grid_max"] + 2
        self.square_tam = cfg.config["screen"]["square_tam"]

        self.characters_num = cfg.config["game"]["characters_num"]
        self._check_config()  # Validate configuration

        # Randomly select which character is player-controlled
        self.controlable_character = random.randint(0, self.characters_num - 1)
        self.BALL_RADIUS = self.square_tam // 2 - cfg.config["screen"]["space_tam"]

    def _init_grid_and_characters(self):
        """
        Generates the grid and initializes all characters (Player and NPCs) with positions and colors.
        """
        # Generate grid and get initial positions for all characters
        self.mainGrid, positions = _generate_grid(
            self.y_grid_max, self.x_grid_max, self.characters_num
        )

        self.characters = []
        for idx, pos in enumerate(positions):
            color = self.COLORS[idx + 1]  # Assign color to each character

            if idx == self.controlable_character:
                # Create player-controlled character
                self.characters.append(
                    Player(idx, pos, color, self.BALL_RADIUS, self.square_tam)
                )
            else:
                # Create NPC character
                self.characters.append(
                    NPC(idx, pos, color, self.BALL_RADIUS, self.square_tam)
                )

    def main_loop(self):
        """
        Main game loop. Handles events, updates game state, and renders the grid.
        """
        running = True
        while running:
            key_down = False  # Track if a valid key was pressed
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False  # Exit loop if window is closed
                elif event.type == pygame.KEYDOWN:
                    key_down = self._handle_keydown(event)  # Handle key press

            if key_down:
                self.turn += 1  # Advance turn
                self._move_npcs()  # Move all NPCs
                self.generate_JSON()  # Output current state

            self.render_grid()  # Draw everything

    def _handle_keydown(self, event):
        """
        Handles keyboard input events for player movement and door state changes.

        Args:
            event (pygame.event.Event): The keyboard event.

        Returns:
            bool: True if a valid action was performed, False otherwise.
        """
        player = self.characters[self.controlable_character]

        # Handle movement keys (1-4)
        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
            new_pos = player.get_move(event)

            # Check if player is moving to the door and the door is open
            if (
                self.mainGrid[new_pos[0], new_pos[1]] == "D"
                and self.door_state == "open"
            ):
                player.move(self.mainGrid, new_pos)
                print("YOU WIN!" if len(self.characters) == 1 else "YOU LOSE!")
                pygame.quit()
                exit()
            else:
                # Move player if possible
                player.move(self.mainGrid, new_pos)
            return True

        # Open the door with key 5
        elif event.key == pygame.K_5:
            self.door_state = "open"
            return True

        # Close the door with key 6
        elif event.key == pygame.K_6:
            self.door_state = "closed"
            return True

        return False  # No valid action

    def _move_npcs(self):
        """
        Moves all NPCs randomly. Removes NPCs that reach the open door.
        """
        npcs_to_remove = []
        for idx, char in enumerate(self.characters):
            if idx != self.controlable_character:
                npc = char
                new_pos = npc.get_random_move(self.mainGrid)
                # If NPC reaches the open door, remove it from the game
                if (
                    self.mainGrid[new_pos[0], new_pos[1]] == "D"
                    and self.door_state == "open"
                ):
                    self.mainGrid[npc.pos] = "."
                    npcs_to_remove.append(npc)
                else:
                    npc.move(self.mainGrid, new_pos)
        # Remove NPCs that exited through the door
        for npc in npcs_to_remove:
            self.characters.remove(npc)

    def generate_JSON(self, action=None, thought=""):
        """
        Generates and prints a JSON-like dictionary with the current simulation state.

        Args:
            action (str, optional): The action performed.
            thought (str, optional): The thought or reasoning for the action.
        """
        # Add current turn's action and thought to memory
        self.memory.append({"turn": self.turn, "action": action, "thought": thought})

        # Build the data dictionary representing the current state
        data = {
            "turn": self.turn,
            "door_state": self.door_state,
            "agents": [
                {"id": char.idx + 1, "x": char.pos[0], "y": char.pos[1]}
                for char in self.characters
            ],
            "ascii_grid": ["".join(row) for row in self.mainGrid.tolist()],
            "button_map": ["btn1", "btn2", "btn3", "btn4", "btn5", "btn6"],
            "memory": self.memory,
        }

        print(data)
        # To return as JSON string: return json.dumps(data, indent=2)

    def render_grid(self):
        """
        Renders the grid and all characters on the Pygame window.
        """
        self.screen.fill((30, 30, 30))  # Fill background

        # Draw grid cells
        for y in range(self.y_grid_max):
            for x in range(self.x_grid_max):
                char = self.mainGrid[y, x]
                rect = pygame.Rect(
                    x * self.square_tam,
                    y * self.square_tam,
                    self.square_tam,
                    self.square_tam,
                )

                if char == "#":
                    # Draw wall cell
                    pygame.draw.rect(self.screen, (100, 100, 100), rect)
                elif char == "D":
                    # Draw door cell
                    pygame.draw.rect(self.screen, (127, 127, 127), rect)
                    if self.door_state == "open":
                        # Draw open door effect
                        dif = self.square_tam // 3
                        rect2 = pygame.Rect(
                            x * self.square_tam + dif // 2,
                            y * self.square_tam + dif // 2,
                            self.square_tam - dif,
                            self.square_tam - dif,
                        )
                        pygame.draw.rect(self.screen, (160, 160, 160), rect2)
                else:
                    # Draw empty cell border
                    pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)

        # Draw all characters (player and NPCs)
        for char in self.characters:
            char.draw(self.screen)

        pygame.display.flip()  # Update the display
        self.clock.tick(60)  # Limit to 60 FPS

    def _print_ascii_grid(self):
        """
        Prints the current grid state as ASCII characters to the console.
        """
        for row in self.mainGrid:
            print(" ".join(row))
        print("\n")

    def _init_pygame(self):
        """
        Initializes the Pygame window and clock.
        """
        pygame.init()
        # Set window size based on grid and square size
        self.screen = pygame.display.set_mode(
            (self.x_grid_max * self.square_tam, self.y_grid_max * self.square_tam)
        )
        pygame.display.set_caption("Grid with Moving Balls")
        self.clock = pygame.time.Clock()

    def _check_config(self):
        """
        Checks if the configuration values are valid for the simulation.

        Raises:
            ValueError: If the number of characters is invalid or exceeds grid capacity.
        """
        # Ensure there are enough grid spaces for all characters
        if self.characters_num > (self.x_grid_max - 2) * (self.y_grid_max - 2):
            raise ValueError("Number of characters exceeds available grid spaces.")

        if self.characters_num < 1:
            raise ValueError("Number of characters must be at least 1.")

        if self.characters_num > 9:
            raise ValueError(
                "Number of characters must be 9 or less to fit in the grid."
            )


if __name__ == "__main__":
    simul = Simulation()
    simul.main_loop()

    pygame.quit()
