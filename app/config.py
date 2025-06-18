import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
DEFAULT_CONFIG = {"default_locale": "en-US"}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)


def get_default_locale() -> str:
    config = load_config()
    return config.get("default_locale", DEFAULT_CONFIG["default_locale"])


def set_default_locale(locale: str) -> None:
    config = load_config()
    config["default_locale"] = locale
    save_config(config)
