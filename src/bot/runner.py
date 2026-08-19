import argparse
import json
from pathlib import Path

from .config import ROOT_DIR, get_target_phone, get_twilio_phone
from .scenarios import SCENARIOS


def build_call_payload(scenario_key: str) -> dict:
    scenario = next((item for item in SCENARIOS if item.key == scenario_key), None)
    if scenario is None:
        raise ValueError(f"Unknown scenario: {scenario_key}")
    return {
        "scenario": scenario.key,
        "title": scenario.title,
        "patient_goal": scenario.patient_goal,
        "target_phone": get_target_phone(),
        "twilio_phone": get_twilio_phone(),
        "transcript_path": str(ROOT_DIR / "artifacts" / "calls" / scenario.key / "transcript.txt"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or inspect voice-bot scenario runs.")
    parser.add_argument("--scenario", choices=[item.key for item in SCENARIOS], default="call_01")
    args = parser.parse_args()
    payload = build_call_payload(args.scenario)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
