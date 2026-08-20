import json
import os
import base64
import urllib.request
from pathlib import Path
from typing import Any

import ngrok
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from openai import OpenAI
from twilio.twiml.voice_response import VoiceResponse

load_dotenv()

app = FastAPI(title="Pretty Good AI Voice Bot")
# In-memory state keyed by Twilio CallSid; enough for this assessment runner.
SESSION_STATE: dict[str, dict[str, Any]] = {}
# All generated artifacts are stored flat by call sid (<sid>.json, <sid>.mp3).
CALLS_DIR = Path(__file__).resolve().parent / "calls"
CALLS_DIR.mkdir(parents=True, exist_ok=True)


def save_recording(call_sid: str, recording_url: str) -> Path:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        raise RuntimeError("Twilio credentials are required to download a recording.")

    audio_path = CALLS_DIR / f"{call_sid}.mp3"
    # Twilio recording URLs require basic auth with account sid + auth token.
    request = urllib.request.Request(f"{recording_url}.mp3")
    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    request.add_header("Authorization", f"Basic {credentials}")
    with urllib.request.urlopen(request, timeout=60) as response:
        audio_path.write_bytes(response.read())
    return audio_path

APPOINTMENT_GOAL = "As a patient, order a prescription."


def connect_ngrok() -> Any:
    token = os.getenv("NGROK_AUTHTOKEN")
    if not token:
        raise RuntimeError(
            "NGROK_AUTHTOKEN is missing. Put it in your .env file or export it in the shell."
        )

    # Expose local FastAPI to Twilio webhooks during local development.
    ngrok.set_auth_token(token)
    forwarder = ngrok.forward("localhost:8000")
    print(f"Available at: {forwarder.url()}")
    return forwarder


def ensure_session(call_sid: str, caller_number: str = "") -> dict[str, Any]:
    # Persist per-call context so each webhook roundtrip has shared memory.
    if call_sid not in SESSION_STATE:
        SESSION_STATE[call_sid] = {
            "call_sid": call_sid,
            "goal": APPOINTMENT_GOAL,
            "caller_number": caller_number,
            "turns": [],
            "ask_count": 0,
            "started": False,
        }
    elif caller_number and not SESSION_STATE[call_sid].get("caller_number"):
        SESSION_STATE[call_sid]["caller_number"] = caller_number
    return SESSION_STATE[call_sid]


def save_transcript(call_sid: str, session: dict[str, Any]) -> None:
    # Persist the latest full turn history after each assistant response.
    transcript_path = CALLS_DIR / f"{call_sid}.json"
    transcript_path.write_text(
        json.dumps(
            {
                "call_sid": call_sid,
                "goal": session["goal"],
                "turns": session["turns"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )




def generate_patient_reply(session: dict[str, Any], user_input: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required. Set it in your .env file.")

    client = OpenAI(api_key=api_key)
    history = session["turns"]
    scenario_goal = session.get("goal", APPOINTMENT_GOAL)
    caller_number = session.get("caller_number", "")
    system_prompt = f"""You are a patient calling a medical office or pharmacy. You're realistic, helpful, and natural in conversation.

SCENARIO: {scenario_goal}

BEHAVIOR:
- Answer directly and naturally, like a real patient would
- Keep responses concise (1-3 sentences) unless more detail is asked
- If asked for personal info (name, DOB, insurance), provide it clearly
- If asked for date of birth, choose one naturally and keep it consistent for the rest of that call
- If the agent asks an unclear question, ask for clarification
- Be cooperative but realistic—show small frustrations if the agent is confusing or repetitive
- Avoid repeating generic responses like "Yes, thank you" unless it is truly the best direct answer
- Never break character or mention AI, testing, or simulations
- Use natural speech patterns, not formal lists
- Phone number is 364-222-4174
- Name is Jordan Lee
- Date of birth is 03/14/1985

CONVERSATION CONTEXT:
You're testing the agent's ability to handle this scenario properly. Be attentive and engaged—if the agent makes errors, you may comment (e.g., "I thought we already discussed that" or "That's not right")."""
    # Replay conversation state each turn so the model stays consistent.
    messages = [{"role": "system", "content": system_prompt}]
    for item in history:
        if item.get("tested_bot"):
            messages.append({"role": "user", "content": item["tested_bot"]})
        if item.get("patient"):
            messages.append({"role": "assistant", "content": item["patient"]})
    messages.append({"role": "user", "content": user_input})
    completion = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages,
        max_tokens=180,
        temperature=0.7,
    )
    result = completion.choices[0].message.content
    return (result or "Could you repeat that?").strip()


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "voice-bot"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/recording-status")
async def recording_status(request: Request) -> Response:
    form = await request.form()
    call_sid = str(form.get("CallSid", "call-default"))
    recording_url = str(form.get("RecordingUrl", "")).strip()

    # Download only finalized recordings to avoid partial/incomplete audio.
    if recording_url and str(form.get("RecordingStatus", "")).lower() == "completed":
        try:
            save_recording(call_sid, recording_url)
        except Exception as error:
            pass

    return Response(status_code=200)


@app.post("/voice")
async def handle_voice(request: Request) -> Response:
    form = await request.form()
    call_sid = str(form.get("CallSid", "call-default"))
    caller_number = str(form.get("From", "")).strip()
    session = ensure_session(call_sid, caller_number)
    session["started"] = True

    # Start with gather-only to prevent talking over the target bot's intro.
    response = VoiceResponse()
    with response.gather(
        input="speech",
        action="/handle-speech",
        method="POST",
        timeout=15,
        speechTimeout=2,
        actionOnEmptyResult=True,
        language="en-US",
    ) as gather:
        pass

    return Response(content=str(response), media_type="application/xml")


@app.post("/handle-speech")
async def handle_speech(request: Request) -> Response:
    form = await request.form()
    call_sid = str(form.get("CallSid", "call-default"))
    user_input = str(form.get("SpeechResult") or form.get("Digits") or "").strip()
    caller_number = str(form.get("From", "")).strip()
    session = ensure_session(call_sid, caller_number)

    if user_input:
        session["turns"].append({"tested_bot": user_input})
        if "done" in user_input.lower():
            reply = "Thank you for your help. Goodbye."
        else:
            reply = generate_patient_reply(session, user_input)
        session["turns"][-1]["patient"] = reply
        save_transcript(call_sid, session)
    else:
        # Silence on empty speech avoids interrupting the other side.
        response = VoiceResponse()
        with response.gather(
            input="speech",
            action="/handle-speech",
            method="POST",
            timeout=10,
            speechTimeout=2,
            actionOnEmptyResult=True,
            language="en-US",
        ):
            pass
        return Response(content=str(response), media_type="application/xml")

    session["ask_count"] += 1
    response = VoiceResponse()
    # Safety stop prevents endless loops if the conversation stalls.
    if "done" in user_input.lower() or session["ask_count"] >= 12:
        response.say(reply, voice="Alice")
        response.hangup()
        save_transcript(call_sid, session)
        return Response(content=str(response), media_type="application/xml")

    with response.gather(
        input="speech",
        action="/handle-speech",
        method="POST",
        timeout=10,
        speechTimeout=2,
        actionOnEmptyResult=True,
        language="en-US",
    ) as gather:
        gather.say(reply, voice="Alice")

    return Response(content=str(response), media_type="application/xml")


@app.post("/media-stream")
def media_stream(request: Request) -> JSONResponse:
    return JSONResponse({"status": "accepted", "note": "Audio stream endpoint ready for Twilio media processing."})


if __name__ == "__main__":
    import uvicorn

    connect_ngrok()
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

