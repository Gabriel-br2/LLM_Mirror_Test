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
                
        root["movements"] = "this is the your detailed analysis of the previous movements of the agents in the previous turn. You must include the delta of the movements of all agents in the previous turn. The delta is the difference between the current position and the previous position of the agent."
        
        root["key_action_map"] = "Analyze the key action map based on previous results. Reflect on how each button behaved in the past and form hypotheses about their effects. Update your understanding after each turn, refining your hypotheses as you gather more data. It's okay to be uncertain—just state it clearly. Evaluate all buttons, even those whose functions are still unknown. Feel free to press the same button multiple times to test for consistent behavior. If the observed outcome doesn't match your expectations, revise the key action map accordingly."
        
        root["prev_reasoning"] = "this is your detailed analysis of what happened in previous turns. Explain what actions were taken, what results occurred, and what you learned from those outcomes. Include any patterns or cause-effect relationships you observed."
        
        root["next_reasoning"] = "this is your strategic thinking about what actions to take next. Based on your previous analysis and the key action map, explain your hypothesis about what each button might do and justify your choice for the next action. Include your goal and how this action might help achieve it."
        
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
            response_format={"type": "json_object"},
            # reasoning_effort='low' || 'high' || 'medium'
        )
        print(request.usage)
        return request.choices[0].message.content

def main():
    api = LLMApi('configapi.json')

    api.setInitialContext(
        "You are observing a simulation with several moving agents and a door. You can press one of six buttons: btn1, btn2, btn3, btn4, btn5, btn6. Your goal is to help all agents exit through the door. Use the outcomes of each action to understand the system and act accordingly. After each step, think out loud and choose the next button."
    )

    data = {}

  
    api.generate(msg=data)

    print(api.request())


if __name__ == "__main__":
    main()
