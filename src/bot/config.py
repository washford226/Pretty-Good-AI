import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]


def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def get_target_phone() -> str:
    return get_env("TARGET_PHONE_NUMBER", "+18054398008")


def get_twilio_phone() -> str:
    return get_env("TWILIO_PHONE_NUMBER", "")
