import os
from pathlib import Path

import uvicorn


def load_env_file() -> None:
    env_candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]

    env_path = next((path for path in env_candidates if path.exists()), None)
    if env_path is None:
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

def main():
    load_env_file()
    port = int(os.getenv("APP_PORT", "5001"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()