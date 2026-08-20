import os

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()


def make_call() -> str:
    # Load required Twilio credentials and runtime options from environment.
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
    target_phone = os.getenv("TARGET_PHONE_NUMBER", "+18054398008")
    app_base_url = os.getenv("APP_BASE_URL")
    # Hard stop to avoid runaway call loops and unnecessary spend.
    call_time_limit = int(os.getenv("CALL_TIME_LIMIT_SECONDS", "180"))

    if not account_sid or not auth_token:
        raise RuntimeError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in the .env file.")
    if not twilio_phone:
        raise RuntimeError("TWILIO_PHONE_NUMBER must be set in the .env file.")
    if not app_base_url:
        raise RuntimeError("APP_BASE_URL must be set in the .env file. Example: https://abcd1234.ngrok-free.app")

    # Create one outbound call into the Pretty Good AI test line.
    client = Client(account_sid, auth_token)
    call = client.calls.create(
        to=target_phone,
        from_=twilio_phone,
        # Twilio starts here and requests TwiML from the local app (via ngrok URL).
        url=f"{app_base_url}/voice",
        method="POST",
        time_limit=call_time_limit,
        # Record the call and notify our app when recording is finalized.
        record=True,
        recording_channels="dual",
        recording_status_callback=f"{app_base_url}/recording-status",
        recording_status_callback_method="POST",
        recording_status_callback_event=["completed"],
    )
    return call.sid


if __name__ == "__main__":
    sid = make_call()
    print(f"Call created successfully. SID: {sid}")
