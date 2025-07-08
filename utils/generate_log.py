import json
import os
from datetime import datetime

class JsonLogger:
    def __init__(self, config_path = 'configapi.json', folder_path='logs'):
        os.makedirs(folder_path, exist_ok=True)
        timestamp = datetime.utcnow().isoformat().replace(":", "-").split(".")[0] + "Z"
        with open(config_path, 'r') as f:
            config_path = json.load(f)
        model_name = config_path['api_model']['model'].replace("/", "_").replace(":", "_")
        self.log_path = os.path.join(folder_path, f"{timestamp}_{model_name}.jsonl")

    def log(self, input_json, output_json):
        
        log_entry = {
            "user_data": json.loads(input_json),
            "llm_data": json.loads(output_json)

        }
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False, indent=4) + '\n\n')

if __name__ == "__main__":
    logger = JsonLogger()

    logger.log({"cmd": "start"}, {"status": "ok"})
    logger.log({"cmd": "step1"}, {"status": "executado"})
    logger.log({"cmd": "end"}, {"status": "finalizado"})

