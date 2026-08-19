# Pretty Good AI Voice Bot

This repo contains the bare essentials for making a real outbound call and saving the resulting call data.

## What is included

- `app.py` — FastAPI Twilio webhook service
- `make_call.py` — places the outbound call
- `record_call_audio.py` — saves recorded audio output
- `listen_to_call.py` — opens the latest saved call metadata/audio
- `start_tunnel.py` — local tunnel helper for Twilio callbacks
- `.env.example` — required environment variables
- `docs/architecture.md` — system overview
- `docs/bug_report.md` — intentionally left blank until live testing begins

## Setup

1. Copy `.env.example` to `.env` and fill in your values.
2. Install dependencies:

   python -m pip install -r requirements.txt

3. Start the app:

   python app.py

4. Start the tunnel if needed:

   python start_tunnel.py

5. Make a call:

   python make_call.py

## Notes

- This project is focused on the call-making and recording flow.
- The bug report is intentionally empty until the actual Pretty Good AI test calls are run and evaluated.
