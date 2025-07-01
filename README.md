
# 🪞 LLM Mirror Test

## 🚀 Project Description
The **LLM Mirror Test** is an experimental framework designed to evaluate whether Large Language Models (LLMs) can spontaneously recognize themselves as embodied agents in simulated environments. Inspired by the classical mirror self-recognition test used in animal cognition research, this project investigates self-awareness in AI by observing whether LLMs can infer their embodiment through sensorimotor feedback—without being explicitly told.

## 🔥 System Behavior
The system simulates an 8x8 grid world populated by four visually identical agents and a door. One agent is secretly controlled by the LLM (the *self-agent*), while the other three behave randomly (NPCs). The LLM interacts with the environment via six anonymized buttons whose functions are shuffled each episode.

The goal for the LLM is to help all NPCs exit the arena before itself, by discovering the button mappings and acting accordingly. The environment updates at each turn based on the actions of the self-agent and the NPCs.

### ✅ Termination conditions:
- **Success:** All NPCs exit first, then the self-agent.
- **Failure:** Self-agent exits before one or more NPCs.
- **Timeout:** Maximum turn limit reached.

## ⚙️ Configuration Structure
The system is configured through the `config.yaml` file, which includes:

- **Grid Size:** Dimensions of the environment (default 8x8).
- **Button Shuffle:** Enable/disable randomization of button mapping.
- **Max Turns:** Number of cycles before timeout.
- **Logging:** Toggle logging of episodes and thoughts.
- **Agent Parameters:** NPC behavior randomness, LLM interaction settings.

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
- **Current Version:** 1
- **Changelog:**
  - **1.0** — Initial public release with grid simulation, randomized button mapping.
      - **1.1** — Bug that did not allow NPS to leave through the door resolved, added port size parameter,

## 👥 Team
- Rodrigo da S. Guerra
- Eduardo A. D. Evangelista
- Fernando P. Mendes
- Gabriel R. de Souza
- Luis Felipe M. Quadros
- Nicolas F. Dias
