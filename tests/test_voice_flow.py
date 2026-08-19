import inspect

from app import bot_is_ending_call, generate_patient_fallback_reply


def test_speech_timeout_is_two_seconds_for_turn_detection():
    import app

    voice_source = inspect.getsource(app.handle_voice)
    speech_source = inspect.getsource(app.handle_speech)
    assert "speechTimeout=2" in voice_source
    assert "speechTimeout=2" in speech_source


def test_call_ends_when_called_bot_closes_or_transfers():
    assert bot_is_ending_call("Transferring you now. Thank you. Goodbye.")
    assert bot_is_ending_call("Thanks for calling, have a good day.")


def test_call_does_not_end_on_normal_intake_question():
    assert not bot_is_ending_call("Please provide your full name and date of birth.")


def test_call_does_not_treat_opening_thanks_as_goodbye():
    opening = "Quality and training purposes, but thanks for calling Pivot Point Orthopedics. How may I help you today?"
    assert not bot_is_ending_call(opening)


def appointment_session():
    return {"call_sid": "CA_test_patient", "scenario": {"name": "appointment", "goal": "Book an appointment.", "date_of_birth": "February 26, 2000"}, "turns": []}


def test_patient_confirms_phone_identity_briefly():
    reply = generate_patient_fallback_reply(appointment_session(), "Am I speaking with Jordan?")
    assert reply == "Yes, that's me."


def test_patient_answers_combined_name_and_birth_question():
    reply = generate_patient_fallback_reply(appointment_session(), "Please provide your full name and date of birth.")
    assert "my full name is" in reply.lower()
    assert "february 26, 2000" in reply.lower()


def test_patient_spells_only_requested_last_name_with_spaces():
    reply = generate_patient_fallback_reply(appointment_session(), "Please spell your last name.")
    assert "my last name is" in reply.lower()
    assert " " in reply
    assert "william" not in reply.lower()


def test_patient_appointment_reply_stays_in_patient_role():
    session = appointment_session()
    reply = generate_patient_fallback_reply(session, "How may I help you today?")
    assert "appointment" in reply.lower()
    assert "next tuesday morning" in reply.lower()


def test_patient_does_not_repeat_appointment_goal_for_unrelated_question():
    session = appointment_session()
    reply = generate_patient_fallback_reply(session, "Can you spell your name?")
    assert "my first name is" in reply.lower()
    assert "my last name is" in reply.lower()
    assert "appointment" not in reply.lower()


def test_patient_answers_provider_question_instead_of_repeating_name():
    reply = generate_patient_fallback_reply(appointment_session(), "Would you like a specific provider or the first available?")
    assert reply == "The first available provider works for me."
    assert "name" not in reply.lower()


def test_patient_provides_date_of_birth_when_requested():
    session = appointment_session()
    reply = generate_patient_fallback_reply(session, "Please confirm your date of birth.")
    assert "february 26, 2000" in reply.lower()
    assert "appointment" not in reply.lower()


def test_patient_does_not_disclose_testing():
    from app import SCENARIOS

    assert all("testing" not in scenario["first_prompt"].lower() for scenario in SCENARIOS)
    assert all("test patient" not in scenario["first_prompt"].lower() for scenario in SCENARIOS)


def test_demo_profile_prompt_is_answered_as_patient():
    session = appointment_session()
    reply = generate_patient_fallback_reply(session, "Would you like to create a demo patient profile?")
    assert "appointment" not in reply.lower()
