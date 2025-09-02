import json
import os
from datetime import datetime, timezone


class JsonLogger:
    def __init__(self, model_name: str = "None", log_dir: str = "logs") -> None:
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-").split(".")[0]
        self.log_path = os.path.join(log_dir, f"{timestamp}.jsonl")

        self.model_name = model_name

    def _write_entry(self, entry: dict) -> None:
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, indent=4) + "\n\n")

    def log_main_data(self, llm_control: dict, button_map: dict) -> None:
        entry = {
            "model": self.model_name,
            "LLM_control": llm_control,
            "button_map": button_map,
        }
        self._write_entry(entry)

    def log(self, user_data, llm_data) -> None:
        if isinstance(user_data, str):
            user_data = json.loads(user_data)
        if isinstance(llm_data, str):
            llm_data = json.loads(llm_data)

        entry = {"user_data": user_data, "llm_data": llm_data}
        self._write_entry(entry)


if __name__ == "__main__":
    logger = JsonLogger()

    logger.log({"cmd": "start"}, {"status": "ok"})
    logger.log({"cmd": "step1"}, {"status": "executado"})
    logger.log({"cmd": "end"}, {"status": "finalizado"})
