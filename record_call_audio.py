import json
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts" / "live_calls"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def record_live_call(call_sid: str, audio_url: str) -> Path:
    out_path = ARTIFACTS_DIR / f"{call_sid}.mp3"
    subprocess.run([
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f"Invoke-WebRequest -Uri '{audio_url}' -OutFile '{out_path}'",
    ], check=False)
    return out_path


def save_call_data(call_sid: str, payload: dict) -> None:
    json_path = ARTIFACTS_DIR / f"{call_sid}.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    print("This helper is ready to be used after a Twilio media callback is available.")
    print("Audio files will be stored under artifacts/live_calls/")
