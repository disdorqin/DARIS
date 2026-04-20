from __future__ import annotations
import json
from pathlib import Path
from agent import LiteratureAgent
def main() -> None:
    payload_path = Path("runtime_input.json")
    payload = {}
    if payload_path.exists():
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    result = LiteratureAgent().run(payload)
    print(json.dumps(result.outputs, ensure_ascii=False))
if __name__ == "__main__":
    main()
