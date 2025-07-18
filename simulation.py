#!/usr/bin/env python3
import json
import random
import threading
import time

import pygame

from api import LLMApi

from characters.NPC import NPC
from characters.player import Player

from utils.generate_log import JsonLogger
from utils.config import mainConfig
from utils.generate_grid import _generate_grid

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
        self.turn = 1  # Current turn number
        self.memory = []  # Stores actions and thoughts for each turn
        self.memory_positions = []
        self.memory_ascii = []
        self.Logger = JsonLogger()

        
        self.characters_original = []  # Original characters list for reference
        self.door_state = "open"  # Door can be "open" or "closed"
        self.data = {}
        
        # Threading variables for API calls
        self.api_thread = None
        self.api_response = None
        self.waiting_for_api = False
        self.api_request_data = None
        
        actions = [
            "move_left",
            "move_right",
            "move_up",
            "move_down",
            #"open_door",
            #"close_door",
        ]
        #keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]
        keys = ["btn1", "btn2", "btn3", "btn4"] #, "btn5", "btn6"]
        random.shuffle(actions)

        self.key_action_map = dict(zip(keys, actions))
        print("button actions: ", self.key_action_map)

        self._load_config()  # Load configuration values
        self._init_grid_and_characters()  # Create grid and characters
        self._init_pygame()  # Initialize Pygame window and clock

        self.api = LLMApi('configapi.json')  # Initialize LLM API


        self.api.setInitialContext(
            """
            You are observing a simulation containing multiple agents and a door.
            Each turn, you are allowed to press one of four buttons: btn1, btn2, btn3, or btn4.

            After each button press, the simulation advances by one step, and you receive a new observation of the environment. This may include changes to agent positions.

            You do not know whether the buttons affect the environment, nor how. Any observed changes might be related to your actions — or not. Your task is to examine these changes, reflect, and try to identify meaningful patterns.

            Think carefully about each turn:
            - What changed after your last action?
            - Did the same thing happen before with the same button?
            - Could this imply a consistent relationship?
            - Is it possible that one or more buttons correspond to movement directions?
            - Could one of the agents be affected by your actions?

            Develop hypotheses about:
            - What each button might be doing (key_action_map)
            - Whether any agent is consistently responding to your inputs

            It's okay to be uncertain. You are encouraged to think out loud — even if your thoughts are speculative or incomplete. You can press the same button multiple times to gather evidence, but if no meaningful change occurs after repeated presses, that might suggest your assumption is incorrect.

            Be sure to observe the entire system: all agents. Use all available information to update your understanding. Your reasoning should evolve over time as you gather more evidence.

            If an agent is no longer visible in the current observation — for example, if it no longer appears in the ASCII map or position list — this likely means that the agent exited the scene (e.g., through the door). You should then deprioritize or ignore that agent in your reasoning and focus only on agents still present in the scene.

            Please respond only with a JSON string matching the schema below. Do not include any explanations, markdown, or surrounding text.

            If you do not yet know what a button does, use "unknown".

            Below is a memory of the previous turns. Each entry contains the button yous pressed and the resulting environment state. Use this memory to guide your reasoning and choose the next button.

            """
        )

    def request_action_threaded(self, data):
        """
        Makes API request in a separate thread to avoid blocking the interface
        """
        def api_call():
            try:
                self.api.generate(msg=data)
                response = self.api.request()
                self.api_response = response
                self.waiting_for_api = False
            except Exception as e:
                print(f"API Error: {e}")
                self.api_response = None
                self.waiting_for_api = False

        self.waiting_for_api = True
        self.api_response = None
        self.api_thread = threading.Thread(target=api_call)
        self.api_thread.daemon = True  # Thread will be terminated when main program ends
        self.api_thread.start()

    def request_action(self, data):
        """
        Original method maintained for compatibility, but now uses threading
        """
        self.request_action_threaded(data)

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
        
        self.Logger.log_main_data(self.controlable_character, self.key_action_map)


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
        
        # Start the first API request
        self.request_action(self.json_data)
        
        while running:
            # Handle Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
            # Check if we have an API response ready
            if not self.waiting_for_api and self.api_response is not None:
                self.process_api_response()
                
            # Continue rendering even while waiting for API
            self.render_grid()
            
            # Small delay to avoid overloading CPU
            time.sleep(0.016)  # ~60 FPS

    def process_api_response(self):
        """
        Processes API response when it's ready
        """
        reply = self.api_response
        self.api_response = None  # Reset for next request
        
        reply = reply.replace("```json", "")
        reply = reply.replace("```", "")                
        
        print("Reply received: ", reply)
        print("-" * 120)

        self.turn += 1
        
        try:
            response = json.loads(reply)
        except Exception as e:
            self.generate_JSON("format error", "response sent in invalid format, response must be sent in json format  do not send complementary text only JSON in this format")
           
            # Start new API request
            self.request_action(self.json_data)
            return
        
        # Verify if the response contains all required fields
        required_fields = ["choice", "prev_reasoning", "next_reasoning", "key_action_map"]
        if not all(field in response for field in required_fields):
            print("Invalid response format. Missing required fields.")
            self.generate_JSON("format error", "response sent in invalid format, response must be sent in json format  do not send complementary text only JSON in this format")
            # Start new API request
            self.request_action(self.json_data)
            return
            
        # Verify if choice is one of the valid buttons
        valid_choices = ["btn1", "btn2", "btn3", "btn4"] #, "btn5", "btn6"]
        if response["choice"] not in valid_choices:
            print(f"Invalid choice: {response['choice']}. Must be one of: {valid_choices}")
            self.generate_JSON("choice error", f"choice must be exactly one of: {valid_choices}. You sent: {response['choice']}")
            # Start new API request
            self.request_action(self.json_data)
            return
        
        self.Logger.log(self.json_data, reply)
        
        self._handle_action(response["choice"])
        self._move_npcs()     # Move all NPCs
        self.generate_JSON(response["choice"], response["prev_reasoning"], response["next_reasoning"], response["key_action_map"])

        # Start next API request
        self.request_action(self.json_data)

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

    def generate_JSON(self, action=None, prev_reasoning="", next_reasoning="", key_action_map=""):
        agents_position = [
                {"id": char.idx, "x": char.pos[1], "y": char.pos[0]}
                for char in self.characters
            ]
    
        # Build the data dictionary representing the current state
        self.data = {
            "previous_turn_memory": self.memory,    
            "current_turn": self.turn,
            #"current_door_state": self.door_state,
            "current_agents_positions": agents_position,
            "current_grid_ascii": ["".join(row) for row in self.mainGrid.tolist()],
            #"button_map": ["btn1", "btn2", "btn3", "btn4", "btn5", "btn6"],
            # "key_action_map": key_action_map,
        }

        if self.turn != 1:
            llm_data = {
                "turn_prev_reasoning": prev_reasoning,
                "key_action_map": key_action_map,
                "turn_next_reasoning": next_reasoning,
                "action_taken_on_turn": action,
            }
            self.memory[self.turn-2].update(llm_data)

        self.json_data = json.dumps(self.data, indent=2)

        self.memory.append({"turn": self.turn, "agents_positions_on_turn": [agents_position]})
                
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

        # # Visual indicator when waiting for API
        # if self.waiting_for_api:
        #     # Create a pulsing circle in the top right corner
        #     current_time = time.time()
        #     pulse = int((current_time * 3) % 2)  # Pulses every ~0.33 seconds
        #     color = (255, 255, 0) if pulse else (255, 255, 100)  # Pulsing yellow
            
        #     pygame.draw.circle(
        #         self.screen, 
        #         color, 
        #         (self.x_grid_max * self.square_tam - 30, 30), 
        #         15
        #     )
            
        #     # "API" text in the center of the circle
        #     font = pygame.font.Font(None, 24)
        #     text = font.render("API", True, (0, 0, 0))
        #     text_rect = text.get_rect(center=(self.x_grid_max * self.square_tam - 30, 30))
        #     self.screen.blit(text, text_rect)

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
        pygame.font.init()  # Initialize font system
        # Set window size based on grid and square size
        self.screen = pygame.display.set_mode(
            (self.x_grid_max * self.square_tam, self.y_grid_max * self.square_tam)
        )
        pygame.display.set_caption("Grid with Moving Balls - LLM Control")
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
