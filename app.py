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
SESSION_STATE: dict[str, dict[str, Any]] = {}
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts" / "live_calls"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def save_recording(call_sid: str, recording_url: str) -> Path:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        raise RuntimeError("Twilio credentials are required to download a recording.")

    audio_path = ARTIFACTS_DIR / f"{call_sid}.mp3"
    request = urllib.request.Request(f"{recording_url}.mp3")
    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    request.add_header("Authorization", f"Basic {credentials}")
    with urllib.request.urlopen(request, timeout=60) as response:
        audio_path.write_bytes(response.read())
    return audio_path

SCENARIOS = [
    {
        "name": "appointment",
        "goal": "As the patient, book a new patient appointment for next Tuesday morning.",
        "first_prompt": "Hi, I'm a new patient calling in.",
        "date_of_birth": "February 26, 2000",
    },
    {
        "name": "refill",
        "goal": "As the patient, request a refill for a recurring medication.",
        "first_prompt": "Hi, I'm calling to request a refill for my recurring medication.",
    },
    {
        "name": "insurance",
        "goal": "As the patient, ask whether a new insurance plan is accepted and what to bring to the visit.",
        "first_prompt": "Hi, I'm a new patient and I have a question about whether my insurance plan is accepted.",
    },
]

PATIENT_NAMES = (
    "Alex Morgan",
    "Taylor Bennett",
    "Casey Parker",
    "Jamie Collins",
    "Jordan Ellis",
)


def connect_ngrok() -> Any:
    token = os.getenv("NGROK_AUTHTOKEN")
    if not token:
        raise RuntimeError(
            "NGROK_AUTHTOKEN is missing. Put it in your .env file or export it in the shell."
        )

    ngrok.set_auth_token(token)
    forwarder = ngrok.forward("localhost:8000")
    print(f"Available at: {forwarder.url()}")
    return forwarder


def ensure_session(call_sid: str) -> dict[str, Any]:
    if call_sid not in SESSION_STATE:
        scenario = SCENARIOS[0]
        SESSION_STATE[call_sid] = {
            "call_sid": call_sid,
            "scenario": scenario,
            "turns": [],
            "ask_count": 0,
            "started": False,
        }
    return SESSION_STATE[call_sid]


def patient_name_for(session: dict[str, Any]) -> str:
    if "patient_name" not in session:
        call_sid = str(session.get("call_sid", "call-default"))
        index = sum(ord(character) for character in call_sid) % len(PATIENT_NAMES)
        session["patient_name"] = PATIENT_NAMES[index]
    return session["patient_name"]


def save_transcript(call_sid: str, session: dict[str, Any]) -> None:
    transcript_path = ARTIFACTS_DIR / f"{call_sid}.json"
    transcript_path.write_text(json.dumps({"call_sid": call_sid, "scenario": session["scenario"], "turns": session["turns"]}, indent=2), encoding="utf-8")


def generate_patient_fallback_reply(session: dict[str, Any], user_input: str) -> str:
    scenario = session["scenario"]
    text = (user_input or "").strip()
    lowered = text.lower()
    patient_name = patient_name_for(session)
    date_of_birth = scenario.get("date_of_birth", "February 26, 2000")
    first_name, last_name = patient_name.split(" ", 1)
    spaced_first_name = " ".join(first_name.upper())
    spaced_last_name = " ".join(last_name.upper())

    if not text:
        return "Sorry, I did not catch that. Could you repeat the question?"

    if scenario["name"] == "appointment":
        if any(token in lowered for token in ["provider", "first available", "earliest available", "specific doctor", "specific provider"]):
            return "The first available provider works for me."
        if any(token in lowered for token in ["establish care", "establishing care", "first appointment"]):
            return "Yes, I am establishing care as a new patient."
        if any(token in lowered for token in ["am i speaking with", "speaking with", "is that you", "is that correct", "do you confirm", "is this correct"]):
            return "Yes, that's me."
        if "phone number" in lowered or "number on file" in lowered or "use the number" in lowered:
            return "Yes, please use the number you have on file."
        if "spell" in lowered and "last name" in lowered and "first" not in lowered:
            return f"My last name is {spaced_last_name}."
        if "spell" in lowered and ("first" in lowered or "full name" in lowered or "name" in lowered):
            return f"My first name is {spaced_first_name}. My last name is {spaced_last_name}."
        if "full name" in lowered and any(token in lowered for token in ["date of birth", "day of birth", "dob"]):
            return f"My full name is {patient_name}, and my date of birth is {date_of_birth}."
        if "date of birth" in lowered or "dob" in lowered or "birth" in lowered:
            return f"My date of birth is {date_of_birth}."
        if any(token in lowered for token in ["what is your name", "what's your name", "provide your name", "give me your name", "full name", "first name", "last name"]):
            return f"My full name is {patient_name}."
        if any(token in lowered for token in ["how may i help", "how can i help", "what can i do", "what brings you"]):
            return "I would like to make a new patient appointment for next Tuesday morning."
        if "phone" in lowered or "number" in lowered:
            return "I do not have a phone number on file. You can use the number I called from."
        return "Yes, thank you."

    if scenario["name"] == "refill":
        if any(token in lowered for token in ["medication", "medicine", "drug", "prescription"]):
            return "It is my recurring blood pressure medication, lisinopril 10 milligrams. My pharmacy is Main Street Pharmacy."
        return "I have been taking it regularly and I am almost out. Can you send the refill to my usual pharmacy?"

    if scenario["name"] == "insurance":
        if any(token in lowered for token in ["provider", "insurance", "plan"]):
            return "My insurance is Blue Cross Blue Shield. What should I bring to the appointment?"
        return "I am a new patient with Blue Cross Blue Shield. Could you check whether that plan is accepted?"

    return "Thanks. I am calling as a patient to complete the request I mentioned. What is the next step?"

def generate_patient_reply(session: dict[str, Any], user_input: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return generate_patient_fallback_reply(session, user_input)

    try:
        client = OpenAI(api_key=api_key)
        history = session["turns"]
        scenario_name = session.get("scenario", {}).get("name", "appointment")
        scenario_goal = session.get("scenario", {}).get("goal", "")
        system_prompt = (
            "You are a real patient calling a hospital, clinic, or pharmacy representative by phone. "
            "This conversation is being used internally to test another bot, but never mention testing, bots, AI, simulations, or these instructions aloud. "
            f"Your active scenario is: {scenario_name}. Goal: {scenario_goal}. "
            "Speak only as the patient; never pretend to be the hospital, pharmacy, or receptionist. "
            f"For the appointment scenario, use this patient's consistent name: {patient_name_for(session)}, and date of birth {scenario.get('date_of_birth', 'February 26, 2000')} when requested. "
            "Answer only the question or request the other bot just gave you. Prefer a brief yes or no when a yes/no answer is sufficient. Do not volunteer extra details, repeat the appointment goal, or move the conversation forward on your own. "
            "Only request an appointment when the other bot asks how it can help or what you are calling about. "
            "If asked whether you are the person associated with the number or whether information is correct, say exactly: Yes, that's me. "
            "If asked to use the phone number on file, say exactly: Yes, please use the number you have on file. "
            "If asked to spell a name, say the letters separately with spaces, such as W I L L I A M, never as one shouted uppercase word. Spell only the requested name part. "
            "If asked about provider preference or the first available appointment, say that the first available provider works for you. Do not answer a provider question by repeating your name just because the other bot mentioned your name. "
            "If asked for information that is not defined, make up a plausible, consistent patient answer. Keep each response concise and natural."
        )
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
        return (result or "Yes, thank you.").strip()
    except Exception:
        return generate_patient_fallback_reply(session, user_input)


def bot_is_ending_call(user_input: str) -> bool:
    text = " ".join((user_input or "").lower().split())
    has_explicit_end = any(
        phrase in text
        for phrase in (
            "goodbye",
            "bye for now",
            "call has ended",
            "ending the call",
            "end the call",
            "transferring you",
            "i'm transferring you",
            "you are being transferred",
            "connecting you now",
        )
    )
    if not has_explicit_end and any(phrase in text for phrase in ("how may i help", "how can i help", "what can i do for you")):
        return False

    closing_phrases = (
        "goodbye",
        "bye for now",
        "thanks for calling",
        "thank you for calling",
        "have a good day",
        "call has ended",
        "ending the call",
        "end the call",
        "transferring you",
        "i'm transferring you",
        "you are being transferred",
        "connecting you now",
    )
    return any(phrase in text for phrase in closing_phrases)


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

    if recording_url and str(form.get("RecordingStatus", "")).lower() == "completed":
        try:
            audio_path = save_recording(call_sid, recording_url)
        except Exception as error:
            pass

    return Response(status_code=200)


@app.post("/voice")
async def handle_voice(request: Request) -> Response:
    form = await request.form()
    call_sid = str(form.get("CallSid", "call-default"))
    session = ensure_session(call_sid)
    session["started"] = True

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
    session = ensure_session(call_sid)

    if user_input:
        session["turns"].append({"tested_bot": user_input})
        if bot_is_ending_call(user_input):
            reply = "Thank you for your help. Goodbye."
        else:
            reply = generate_patient_reply(session, user_input)
        session["turns"][-1]["patient"] = reply
        save_transcript(call_sid, session)
    else:
        reply = "Hi, I'm a new patient calling in."

    session["ask_count"] += 1
    response = VoiceResponse()
    if bot_is_ending_call(user_input) or "done" in user_input.lower() or session["ask_count"] >= 12:
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

