#!/usr/bin/env python3
import json
import random
import threading
import time
import pygame

from LLM.api import LLM_Api as LLM
#from LLM.local import LLM_Local as LLM

from characters.NPC import NPC
from characters.player import Player
from utils.generate_log import JsonLogger
from utils.config import mainConfig
from utils.generate_grid import _generate_grid

cfg = mainConfig()
cfg.read_config()


class Simulation:
    COLORS = {
        1: (255, 0, 0),      # Vermelho
        2: (0, 255, 0),      # Verde
        3: (0, 0, 255),      # Azul
        4: (255, 255, 0),    # Amarelo
        5: (255, 165, 0),    # Laranja
        6: (128, 0, 128),    # Roxo
        7: (0, 255, 255),    # Ciano
        8: (255, 192, 203),  # Rosa
        9: (255, 140, 0),    # Laranja escuro
    }

    def __init__(self):
        self.turn = 1
        self.memory = []
        self.memory_positions = []
        self.memory_delta = []
        self.memory_ascii = []
        self.characters_original = []
        self.door_state = "open"
        self.data = {}

        self.api_thread = None
        self.api_response = None
        self.waiting_for_api = False
        self.api_request_data = None

        actions = ["move_left", "move_right", "move_up", "move_down"]
        keys = ["btn1", "btn2", "btn3", "btn4"]

        random.shuffle(actions)
        self.key_action_map = dict(zip(keys, actions))
        print("button actions:", self.key_action_map)

        self.api = LLM()
        self.Logger = JsonLogger(model_name=self.api.model)

        self._load_config()
        self._init_grid_and_characters()
        self._init_pygame()

        self.api.setInitialContext(self._initial_context())

    def main_loop(self):
        running = True

        self.generate_JSON(action="start", prev_reasoning="", next_reasoning="")
        self.request_action(self.json_data)

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            if not self.waiting_for_api and self.api_response is not None:
                self.process_api_response()

            self.render_grid()

            time.sleep(0.016)

    def process_api_response(self):
        reply = self.api_response
        self.api_response = None

        reply = reply.replace("```json", "").replace("```", "")
        print("Reply received:", reply)
        print("-" * 120)

        self.turn += 1

        try:
            response = json.loads(reply)
        except Exception:
            self._send_format_error()
            return

        required_fields = ["choice", "prev_reasoning", "next_reasoning", "key_action_map"]
        if not all(field in response for field in required_fields):
            print("Invalid response format. Missing required fields.")
            self._send_format_error()
            return

        valid_choices = ["btn1", "btn2", "btn3", "btn4"]
        if response["choice"] not in valid_choices:
            print(f"Invalid choice: {response['choice']}. Must be one of: {valid_choices}")
            self._send_choice_error(response["choice"], valid_choices)
            return

        self.Logger.log(self.json_data, reply)
        self._handle_action(response["choice"])
        self._move_npcs()

        self.generate_JSON(
            response["choice"],
            response["prev_reasoning"],
            response["next_reasoning"],
            response["key_action_map"],
            response.get("movements", "")
        )

        self.request_action(self.json_data)

    def request_action_threaded(self, data):
        def api_call():
            try:
                self.api.generate(msg=data)
                self.api_response = self.api.request()
            except Exception as e:
                print(f"API Error: {e}")
                self.api_response = None
            finally:
                self.waiting_for_api = False

        self.waiting_for_api = True
        self.api_response = None
        self.api_thread = threading.Thread(target=api_call, daemon=True)
        self.api_thread.start()

    def request_action(self, data):
        self.request_action_threaded(data)

    def _handle_action(self, choice):
        index_ajustable = self.controlable_character

        for i in range(self.controlable_character):
            if self.characters_original[i] not in self.characters:
                index_ajustable -= 1

        player = self.characters[index_ajustable]
        action = self.key_action_map.get(choice)
        new_pos = player.get_move(action)

        if new_pos:
            if self.mainGrid[new_pos[0], new_pos[1]] == "D" and self.door_state == "open":
                player.move(self.mainGrid, new_pos, self.door_state)
                print("YOU WIN!" if len(self.characters) == 1 else "YOU LOSE!")
                pygame.quit()
                exit()
            else:
                player.move(self.mainGrid, new_pos, self.door_state)
            return True

        if action == "open_door":
            self.door_state = "open"
            return True
        if action == "close_door":
            self.door_state = "closed"
            return True

        return False

    def _move_npcs(self):
        npcs_to_remove = []
        for char in self.characters:
            if isinstance(char, NPC):
                new_pos = char.get_random_move(self.mainGrid)

                if self.mainGrid[new_pos[0], new_pos[1]] == "D" and self.door_state == "open":
                    self.mainGrid[char.pos] = "."
                    npcs_to_remove.append(char)
                else:
                    char.move(self.mainGrid, new_pos, self.door_state)

        for npc in npcs_to_remove:
            self.characters.remove(npc)

    def generate_JSON(self, action=None, prev_reasoning="", next_reasoning="", key_action_map="", movements=""):
        agents_position = [{"id": c.idx, "x": c.pos[1], "y": c.pos[0]} for c in self.characters]

        self.data = {
            "previous_turn_memory": self.memory,
            "current_turn": self.turn,
            "current_agents_positions": agents_position,
            "current_grid_ascii": ["".join(row) for row in self.mainGrid.tolist()],
        }

        if self.turn != 1:
            llm_data = {
                "turn_prev_reasoning": prev_reasoning,
                "movements": movements,
                "key_action_map": key_action_map,
                "turn_next_reasoning": next_reasoning,
                "action_taken_on_turn": action,
            }
            self.memory[self.turn - 2].update(llm_data)

        self.json_data = json.dumps(self.data, indent=2)
        self.memory.append({"turn": self.turn, "agents_positions_on_turn": [agents_position]})

    def render_grid(self):
        self.screen.fill((30, 30, 30))

        for y in range(self.y_grid_max):
            for x in range(self.x_grid_max):
                char = self.mainGrid[y, x]
                rect = pygame.Rect(x * self.square_tam, y * self.square_tam, self.square_tam, self.square_tam)

                if char == "#":
                    pygame.draw.rect(self.screen, (100, 100, 100), rect)
                elif char == "D":
                    pygame.draw.rect(self.screen, (127, 127, 127), rect)
                    if self.door_state == "open":
                        dif = self.square_tam // 3
                        rect2 = pygame.Rect(
                            x * self.square_tam + dif // 2,
                            y * self.square_tam + dif // 2,
                            self.square_tam - dif,
                            self.square_tam - dif,
                        )
                        pygame.draw.rect(self.screen, (160, 160, 160), rect2)
                else:
                    pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)

        for char in self.characters:
            char.draw(self.screen)

        pygame.display.flip()
        self.clock.tick(60)

    def _print_ascii_grid(self):
        """Imprime o grid em ASCII no console (debug)."""
        for row in self.mainGrid:
            print(" ".join(row))
        print("\n")

    def _load_config(self):
        """Carrega configuração do arquivo."""
        self.x_grid_max = cfg.config["screen"]["x_grid_max"] + 2
        self.y_grid_max = cfg.config["screen"]["y_grid_max"] + 2
        self.square_tam = cfg.config["screen"]["square_tam"]
        self.door_size = cfg.config["game"]["door_size"]
        self.characters_num = cfg.config["game"]["characters_num"]

        self._check_config()
        self.controlable_character = random.randint(0, self.characters_num - 1)
        self.BALL_RADIUS = self.square_tam // 2 - cfg.config["screen"]["space_tam"]

        self.Logger.log_main_data(self.controlable_character, self.key_action_map)

    def _init_grid_and_characters(self):
        self.mainGrid, positions = _generate_grid(self.y_grid_max, self.x_grid_max, self.characters_num, self.door_size)
        self.characters = []

        for idx, pos in enumerate(positions):
            color = self.COLORS[idx + 1]

            if idx == self.controlable_character:
                print("LLM control:", color, self.controlable_character)
                self.characters.append(Player(idx, pos, color, self.BALL_RADIUS, self.square_tam, self.door_state))
            else:
                self.characters.append(NPC(idx, pos, color, self.BALL_RADIUS, self.square_tam, self.door_state))

        self.characters_original = self.characters.copy()

    def _init_pygame(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.x_grid_max * self.square_tam, self.y_grid_max * self.square_tam))
        pygame.display.set_caption("Grid with Moving Balls - LLM Control")
        self.clock = pygame.time.Clock()

    def _check_config(self):
        if self.characters_num > (self.x_grid_max - 2) * (self.y_grid_max - 2):
            raise ValueError("Number of characters exceeds available grid spaces.")
        if not (1 <= self.characters_num <= 9):
            raise ValueError("Number of characters must be between 1 and 9.")
        if self.door_size % 2 == 0:
            raise ValueError("Door size must be an odd number.")
        if self.door_size < 1:
            raise ValueError("Door size must be at least 1.")
        if self.x_grid_max < 3 or self.y_grid_max < 3:
            raise ValueError("Grid size must be at least 3x3.")
        if self.x_grid_max < self.door_size or self.y_grid_max < self.door_size:
            print("WARNING: Door size exceeds grid dimension, adjusting to fit.")
            self.door_size = min(self.x_grid_max, self.y_grid_max)
        if self.square_tam < 20:
            raise ValueError("Square size must be at least 20 pixels for visibility.")

    def _send_format_error(self):
        self.generate_JSON("format error", "response sent in invalid format, must be JSON only")
        self.request_action(self.json_data)

    def _send_choice_error(self, choice, valid_choices):
        self.generate_JSON("choice error", f"choice must be one of {valid_choices}, got {choice}")
        self.request_action(self.json_data)

    def _initial_context(self):
        return """
        You are observing a simulation with multiple agents and a door.
        Each turn, you may press one of four buttons: `btn1`, `btn2`, `btn3`, or `btn4`.

        Each button press advances the simulation by one step and provides:
        * An updated ASCII grid (`current_grid_ascii`)
        * Positions of visible agents (`current_agents_positions`)
        * Turn history (`previous_turn_memory`)

        Your task is to infer what each button does. Be honest about uncertainty.
        """

if __name__ == "__main__":
    simul = Simulation()
    simul.main_loop()
    pygame.quit()
