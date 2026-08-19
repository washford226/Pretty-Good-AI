import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts" / "live_calls"


def list_calls() -> list[Path]:
    if not ARTIFACTS_DIR.exists():
        return []
    return sorted(ARTIFACTS_DIR.glob("*.json"))


def play_latest() -> None:
    files = list_calls()
    if not files:
        print("No recorded calls found yet. Make a call first.")
        return

    latest = files[-1]
    print(f"Playing latest transcript: {latest.name}")
    print(latest.read_text(encoding="utf-8"))

    audio_path = latest.with_suffix(".mp3")
    if audio_path.exists():
        if os.name == "nt":
            os.startfile(str(audio_path))
        else:
            subprocess.run(["open", str(audio_path)], check=False)
    else:
        print("No matching .mp3 audio file was found for this call yet.")


if __name__ == "__main__":
    play_latest()
