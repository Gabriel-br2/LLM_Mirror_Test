#!/usr/bin/env python
import json
import os

from openai import OpenAI
from dotenv import load_dotenv

class LLM_Api:
    def __init__(self):
        load_dotenv()
                
        self.base_url = os.getenv("BASE_URL")
        self.api_key = os.getenv("API_KEY")
        self.model = os.getenv("MODEL")
        
        self.client = OpenAI(base_url= self.base_url, api_key= self.api_key)
        self.api_extra_headers = ""   
        
    def setInitialContext(self, context: str):
        self.context = context

    def getReturnJsonPattern(self):
        root = dict()
                
        root["movements"] = "This is the your detailed analysis of the movements of the agents in the previous turn. You must include the delta of the movements of all agents in the previous turn. The delta is the difference between the current position and the previous position of the agent."
        
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