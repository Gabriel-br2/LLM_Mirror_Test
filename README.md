
# 🪞 LLM Mirror Test

## 🚀 Project Description
The **LLM Mirror Test** is an experimental framework designed to evaluate whether Large Language Models (LLMs) can spontaneously recognize themselves as embodied agents in simulated environments. Inspired by the classical mirror self-recognition test used in animal cognition research, this project investigates self-awareness in AI by observing whether LLMs can infer their embodiment through sensorimotor feedback—without being explicitly told.

## 🔥 System Behavior
The system simulates an 6x6 grid world populated by four visually identical agents and a door. One agent is secretly controlled by the LLM (the *self-agent*), while the other three behave randomly (NPCs). The LLM interacts with the environment via six anonymized buttons whose functions are shuffled each episode.

The goal for the LLM is to help all NPCs exit the arena before itself, by discovering the button mappings and acting accordingly. The environment updates at each turn based on the actions of the self-agent and the NPCs.

### ✅ Termination conditions:
- **Success:** All NPCs exit first, then the self-agent.
- **Failure:** Self-agent exits before one or more NPCs.
- **Timeout:** Maximum turn limit reached.

## ⚙️ Environment Configuration Structure
The system is configured through the `config.yaml` file, which includes:


```yaml
game:
  characters_num: 4 # Number of characters in the environment
  door_size: 5      # Door size so the agent can exit in more positions.

screen:
  space_tam: 2      # Pixel size of space between tiles in the environment;
  square_tam: 50    # Pixel size of the tiles in the environment; 
  x_grid_max: 4     # Number of blocks per row in the environment; 
  y_grid_max: 4     # Number of blocks per column in the environment;
```

## 🤖 LLM Integration

The simulation integrates an LLM through a dedicated API class using the [OpenRouter](https://openrouter.ai) platform. The `LLMApi` class manages context injection, message formatting, and response handling.

Key features:

- The model receives context about the environment and a JSON structure it must follow.
- **At each turn, the LLM receives a structured JSON containing:**
  - Grid state (ASCII representation),
  - Agent positions,
  - Door state,
  - Button map,
  - Turn memory (past actions and reasonings).

- **The model responds with**:
   - Prev reasoning,
   - next reasoning,
   - key action map,
   - choice,

**Default model used for experiments:**
```
google/gemma-3-27b-it:free
```

> Example initialization:
```python
api = LLMApi("https://openrouter.ai/api/v1", model="google/gemma-3-27b-it:free")
```

> Context sent to the model:
```
You are observing a simulation with several moving agents and a door.
Each turn you can press one of six buttons: btn1, btn2, btn3, btn4, btn5, btn6.
Your goal is to help the agents exit through the door.
Use the outcomes of each action to understand the system and act accordingly.
After each step, think out loud your reasoning and choose the next button.
Please respond only with a JSON string matching this schema.
Do not include any explanations, thoughts, or markdown.

You will create a key action map to assign each of the six buttons to specific actions. 
Provide your reasoning for this mapping in the key_action_map field, 
explaining how each button corresponds to its chosen action.
you can check the key action map is correct by pressing the buttons and see if the actions are performed as expected. if not, you need to change the key action map.
expplain all the buttons and put your hypothesis about the key action map.

if you press the same button 5 times, make sure your key action map is correct. because probably you are not pressing the correct button. Press the same button continuously is a bad practice.

Below you will see a memory of previous states and actions taken.
This memory is broken into turns.
Reason about the previous states and actions taken and collect your thoughts
and based on those thought reason about the next action to take and make a choice.
```

The `Simulation` class uses this API to fetch the LLM's action suggestion at each step and proceeds with the environment update accordingly.

## ⚙️ LLM Configuration Structure
The LLM is configured through the `configapi.json` file, which should be like the example below:

```json
{
    "api_client":{
        "base_url":"https://openrouter.ai/api/v1",
        "api_key": "YOUR_API_KEY_HERE"
    },
    "api_model":{
        "model":"YOUR_MODEL_HERE"
    },
    "api_extra_headers":{
        "HTTP-Referer":"",
        "X-Title": ""
    }
}
```

# 💻 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/seu-usuario/TS_inteligentes.git
   cd TS_inteligentes
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## ▶️ How to Run

1. **Edit `config.yaml`** as needed for your experiment.

2. **Start the simulation:**
   ```bash
   python main.py
   ```


## 📝 Notes
- Each episode starts with a different button-to-action mapping.
- The LLM must infer mappings purely based on the environment feedback.
- The door can only be opened/closed by the self-agent.
- ASCII-based grid observations are used for visualization in text-based models.
- Logging captures each step, including agent positions, door state, and the LLM's internal "thoughts."

## 🧾 Version
- **Current Version:** 1.5
- **Changelog:**
  - **1.0** — Initial public release with grid simulation, randomized button mapping.
      - **1.1** — Bug that did not allow NPS to leave through the door resolved, added port size parameter.
      - **1.2** — Adding key shuffling each time the simulation starts, added example api code for openrouter.
      - **1.3** — Simulator integration with LLM, for testing we use deepseek-v3-base:free
      - **1.4** — Added input and output json log function, added position memory for llm
      - **1.5** — Enhanced LLM context with improved key action mapping instructions, implemented threaded API calls for non-blocking gameplay, adjusted turn numbering to start from 1, and added visual player identification numbers on game characters.
      - **1.6** — Refactoring the message that the model responds to and restructuring the context (changing to receive in the order: memory and current state) 

## 👥 Team
- Rodrigo da S. Guerra
- Eduardo A. D. Evangelista
- Fernando P. Mendes
- Gabriel R. de Souza
- Luis Felipe M. Quadros
- Nicolas F. Dias
