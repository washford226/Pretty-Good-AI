import os
from typing import Any

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()


def get_twilio_client() -> Client:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        raise RuntimeError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set to make a live outbound call.")
    return Client(account_sid, auth_token)


def place_call(to_number: str, from_number: str, twiml_url: str) -> Any:
    client = get_twilio_client()
    return client.calls.create(
        to=to_number,
        from_=from_number,
        url=twiml_url,
        method="POST",
    )
