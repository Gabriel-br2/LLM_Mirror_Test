#!/usr/bin/env python3
import json
import random

import pygame

from api import LLMApi

from characters.NPC import NPC
from characters.player import Player

from utils.generate_log import JsonLogger
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
        Initializes the simulation, loads configuration, creates grid and characters
        """
        self.turn = 0  # Current turn number
        self.memory = []  # Stores actions and thoughts for each turn
        self.memory_positions = []
        self.memory_ascii = []
        self.Logger = JsonLogger()
        
        self.characters_original = []  # Original characters list for reference
        self.door_state = "closed"  # Door can be "open" or "closed"
        self.data = {}
        
        actions = [
            "move_left",
            "move_right",
            "move_up",
            "move_down",
            "open_door",
            "close_door",
        ]
        #keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]
        keys = ["btn1", "btn2", "btn3", "btn4", "btn5", "btn6"]
        random.shuffle(actions)

        self.key_action_map = dict(zip(keys, actions))
        print("button actions: ", self.key_action_map)

        self._load_config()  # Load configuration values
        self._init_grid_and_characters()  # Create grid and characters
        self._init_pygame()  # Initialize Pygame window and clock

        self.api = LLMApi('configapi.json')  # Initialize LLM API

        self.api.setInitialContext(
            "You are observing a simulation with several moving agents and a door. " \
            "Each turn you can press one of six buttons: btn1, btn2, btn3, btn4, btn5, btn6. " \
            "Your goal is to help the agents exit through the door. " \
            "Use the outcomes of each action to understand the system and act accordingly. " \
            "After each step, think out loud your reasoning and choose the next button. " \
            "Please respond only with a JSON string matching this schema. " \
            "Do not include any explanations, thoughts, or markdown. " \
            "Below you will see a memory of previous states and actions taken. " \
            "This memory is broken into turns. " \
            "Reason about the previous states and actions taken and collect your thoughts " \
            "and based on those thought reason about the next action to take and make a choice."
        )

    def request_action(self,data):
        self.api.generate(msg=data)
        return self.api.request()

        # self._print_ascii_grid()  # Uncomment to print grid in ASCII

    def _load_config(self):
        """
        Loads configuration values from the config file and sets simulation parameters.
        """
        # Add 2 to grid size for borders
        self.x_grid_max = cfg.config["screen"]["x_grid_max"] + 2
        self.y_grid_max = cfg.config["screen"]["y_grid_max"] + 2
        self.square_tam = cfg.config["screen"]["square_tam"]
        self.door_size = cfg.config["game"]["door_size"]

        self.characters_num = cfg.config["game"]["characters_num"]
        self._check_config()

        # Randomly select which character is player-controlled
        self.controlable_character = random.randint(0, self.characters_num - 1)
        self.BALL_RADIUS = self.square_tam // 2 - cfg.config["screen"]["space_tam"]

    def _init_grid_and_characters(self):
        """
        Generates the grid and initializes all characters (Player and NPCs) with positions and colors.
        """
        # Generate grid and get initial positions for all characters
        self.mainGrid, positions = _generate_grid(
            self.y_grid_max, self.x_grid_max, self.characters_num, self.door_size
        )

        self.characters = []
        for idx, pos in enumerate(positions):
            color = self.COLORS[idx + 1]  # Assign color to each character

            if idx == self.controlable_character:
                # Create player-controlled character
                print("LLM control:", color, self.controlable_character)
                self.characters.append(
                    Player(
                        idx,
                        pos,
                        color,
                        self.BALL_RADIUS,
                        self.square_tam,
                        self.door_state,
                    )
                )
            else:
                # Create NPC character
                self.characters.append(
                    NPC(
                        idx,
                        pos,
                        color,
                        self.BALL_RADIUS,
                        self.square_tam,
                        self.door_state,
                    )
                )

        self.characters_original = self.characters.copy()

    def main_loop(self):
        """
        Main game loop. Handles events, updates game state, and renders the grid.
        """
        running = True
        self.generate_JSON(action="start", prev_reasoning="", next_reasoning="")  # Initial state
        
        f = 0
        while running:
            f += 1
            key_down = False  # Track if a valid key was pressed
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False  # Exit loop if window is closed
                #elif event.type == pygame.KEYDOWN:
                #    key_down = self._handle_keydown(event)  # Handle key press

            if (f % 2 == 0):
                reply = self.request_action(self.json_data)
                
                reply = reply.replace("```json", "")
                reply = reply.replace("```", "")                
                
                #print(self.data)
                print("Reply received: ", reply)
                print("-" * 100)

                # Advance turn
                self.turn += 1
                
                try:
                    response = json.loads(reply)
                except:
                    self.generate_JSON("format error", "response sent in invalid format, response must be sent in json format {'thought': 'this is your thoughts', 'choice': 'this your choice'} do not send complementary text only JSON in this format")
                    continue
                
                self.Logger.log(self.json_data, reply)
                
                self._handle_action(response["choice"])

                self._move_npcs()     # Move all NPCs
                self.generate_JSON(response["choice"], response["prev_reasoning"], response["next_reasoning"])

            self.render_grid()  # Draw everything
                # self._print_ascii_grid()

    def _handle_action(self, choice):
        """
        Handles randomized keyboard input events.

        Args:
            event (pygame.event.Event): The keyboard event.

        Returns:
            bool: True if a valid action was performed, False otherwise.
        """
        index_ajustable = self.controlable_character
        for i in range(self.controlable_character):
            if self.characters_original[i] not in self.characters:
                index_ajustable -= 1
        player = self.characters[index_ajustable]

        action = self.key_action_map.get(choice)
        new_pos = player.get_move(action)

        if new_pos:
            if (
                self.mainGrid[new_pos[0], new_pos[1]] == "D"
                and self.door_state == "open"
            ):
                player.move(self.mainGrid, new_pos, self.door_state)
                print("YOU WIN!" if len(self.characters) == 1 else "YOU LOSE!")
                pygame.quit()
                exit()
            else:
                player.move(self.mainGrid, new_pos, self.door_state)
            return True

        elif action == "open_door":
            self.door_state = "open"
            return True

        elif action == "close_door":
            self.door_state = "closed"
            return True

        return False

    def _move_npcs(self):
        """
        Moves all NPCs randomly. Removes NPCs that reach the open door.
        """
        npcs_to_remove = []
        for idx, char in enumerate(self.characters):

            if type(self.characters[idx]) == NPC:
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
                    npc.move(self.mainGrid, new_pos, self.door_state)

        # Remove NPCs that exited through the door
        for npc in npcs_to_remove:
            self.characters.remove(npc)

    def generate_JSON(self, action=None, prev_reasoning="", next_reasoning=""):
        """
        Generates and prints a JSON-like dictionary with the current simulation state.

        Args:
            action (str, optional): The action performed.
            thought (str, optional): The thought or reasoning for the action.
        """
        # Add current turn's action and thought to memory

        agents_position = [
                {"id": char.idx + 1, "x": char.pos[0], "y": char.pos[1]}
                for char in self.characters
            ]
    
        # Build the data dictionary representing the current state
        self.data = {
            "current_turn": self.turn,
            "door_state": self.door_state,
            "current_agents_positions": agents_position,
            "ascii_grid": ["".join(row) for row in self.mainGrid.tolist()],
            "button_map": ["btn1", "btn2", "btn3", "btn4", "btn5", "btn6"],
            "turn_memory": self.memory    
        }

        if self.turn != 0:
            llm_data = {
                "action_taken_on_turn": action,
                "turn_prev_reasoning": prev_reasoning,
                "turn_next_reasoning": next_reasoning
            }
            self.memory[self.turn-1].update(llm_data)

        self.json_data = json.dumps(self.data, indent=2)

        self.memory.append({"turn": self.turn, "turn_door_state": self.door_state, "agents_positions_on_turn": [agents_position]})
                
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

        if self.door_size % 2 == 0:
            raise ValueError("Door size must be an odd number.")

        if self.door_size < 1:
            raise ValueError("Door size must be at least 1.")

        if self.x_grid_max < 3 or self.y_grid_max < 3:
            raise ValueError(
                "Grid size must be at least 3x3 to accommodate walls and characters."
            )

        if self.x_grid_max < self.door_size:
            print("WARNING: Door size exceeds grid width, adjusting to fit.")
            self.door_size = self.x_grid_max

        elif self.y_grid_max < self.door_size:
            print("WARNING: Door size exceeds grid width, adjusting to fit.")
            self.door_size = self.y_grid_max

        if self.square_tam < 20:
            raise ValueError("Square size must be at least 20 pixels for visibility.")


if __name__ == "__main__":
    simul = Simulation()
    simul.main_loop()
    pygame.quit()
