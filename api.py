#!/usr/bin/env python
import json
import os

from openai import OpenAI


class LLMApi:
    def __init__(self, config_path: str):
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, config_path)
        try:
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
                self.client = OpenAI(base_url= config['api_client']['base_url'],
                                     api_key= config['api_client']['api_key'])
                self.model = config['api_model']['model']
                self.api_extra_headers = config['api_extra_headers'].get('extra_headers', {})
        except FileNotFoundError:
            print(f"Configuration file not found at {config_path}")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON from the configuration file at {config_path}")
            return None 

    def setInitialContext(self, context: str):
        self.context = context

    def getReturnJsonPattern(self) -> dict:
        root = dict()
        root["prev_reasoning"] = "this is your reasoning about previous actions"
        root["next_reasoning"] = "this is your reasoning about next actions to take"
        root["key_action_map"] = "this is your reasoning about the key action map"
        root["choice"] = "this your button choice"
        return root

    def generate(self, msg: dict):
        self.payload = "<context>\n"
        self.payload += self.context
        self.payload += "\nFollow the bellow json to answer:\n"
        self.payload += json.dumps(self.getReturnJsonPattern(), indent=2)
        self.payload += "\n</context>\n"
        self.payload += "<current_turn>\n"
        self.payload += json.dumps(msg, indent=2)
        self.payload += "\n</current_turn>\n"

    def request(self) -> str:
        request = self.client.chat.completions.create(
            model=self.model, 
            messages=[{"role": "user", "content": self.payload}],
            response_format={"type": "json_object"}
        )
        return request.choices[0].message.content

def main():
    api = LLMApi('configapi.json')

    api.setInitialContext(
        "You are observing a simulation with several moving agents and a door. You can press one of six buttons: btn1, btn2, btn3, btn4, btn5, btn6. Your goal is to help all agents exit through the door. Use the outcomes of each action to understand the system and act accordingly. After each step, think out loud and choose the next button."
    )

    data = {}

    data = {'turn': 0, 'door_state': 'closed', 'agents': [{'id': 1, 'x': 4, 'y': 4}, {'id': 2, 'x': 5, 'y': 8}, {'id': 3, 'x': 8, 'y': 5}, {'id': 4, 'x': 1, 'y': 5}], 'ascii_grid': ['######DDD#', '#....4...#', '#........#', '#........#', '#...1....#', '#.......2#', '#........#', '#........#', '#....3...#', '##########'], 'button_map': ['btn1', 'btn2', 'btn3' 'btn4', 'btn5', 'btn6'], 'memory': [{'turn': 0, 'action': 'start', 'thought': ''}]}

    api.generate(msg=data)

    print(api.request())


if __name__ == "__main__":
    main()
