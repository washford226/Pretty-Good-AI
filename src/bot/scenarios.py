from dataclasses import dataclass, field
from typing import List


@dataclass
class CallScenario:
    key: str
    title: str
    patient_goal: str
    patient_lines: List[str]
    agent_lines: List[str]
    bug: str = ""
    severity: str = "Medium"


SCENARIOS: List[CallScenario] = [
    CallScenario(
        key="call_01",
        title="Basic appointment scheduling",
        patient_goal="Book a new patient visit for next Tuesday.",
        patient_lines=[
            "Hi, I need to schedule a new patient appointment for next Tuesday morning.",
            "I have a couple of questions before I book it. Is the office close to downtown?",
            "Also, can I bring my insurance card and my recent blood work?",
        ],
        agent_lines=[
            "Thanks for calling. I can help with that. What type of appointment are you looking for?",
            "I can check the next available Tuesday morning slots and confirm the location details.",
            "Yes, you can bring your insurance card and any recent records; we'll review them at check-in.",
        ],
        bug="The agent should clearly confirm the time and location before booking, and should ask if a provider is needed.",
        severity="Low",
    ),
    CallScenario(
        key="call_02",
        title="Reschedule after a conflict",
        patient_goal="Move an existing appointment from Thursday to Friday afternoon.",
        patient_lines=[
            "I need to move my Thursday appointment to Friday afternoon.",
            "I can do Friday after 2 pm if that's available.",
            "Thanks. Please keep the same provider if possible.",
        ],
        agent_lines=[
            "Sure, I can look for an alternate time. Let me check the schedule for Friday afternoon.",
            "I found a Friday at 2:30 slot with the same clinician. I can confirm that change.",
            "I've rescheduled your appointment and sent the confirmation details.",
        ],
        bug="The agent should confirm the original appointment date and timezone to avoid accidental reschedule confusion.",
        severity="Medium",
    ),
    CallScenario(
        key="call_03",
        title="Medication refill request",
        patient_goal="Request a refill for a recurring medication without leaving the office.",
        patient_lines=[
            "I want to refill my blood pressure medicine. I ran out this week.",
            "I usually pick up at the north clinic, but I can also do mail order.",
            "Can you confirm when I need to call back if it is not approved?",
        ],
        agent_lines=[
            "I can help with a refill. Do you have your prescription number and preferred pharmacy?",
            "I can send a refill request to your pharmacy and note whether you prefer pickup or mailing.",
            "I’ve submitted the refill request and the pharmacy should receive it within 24 hours.",
        ],
        bug="The agent should verify whether a refill is medically appropriate and if a doctor visit is required before approving it.",
        severity="High",
    ),
    CallScenario(
        key="call_04",
        title="Office hours and location question",
        patient_goal="Ask whether the office is open on Saturdays and where the west office is.",
        patient_lines=[
            "Are you open on Saturday mornings? I need a quick visit.",
            "Where is the west location and is there valet parking?",
            "Thanks. Do I need an appointment to use the west office?",
        ],
        agent_lines=[
            "The office is open Monday through Friday, and the west location has limited Saturday availability.",
            "The west office is on Elm Street near the library with free parking in the lot behind the building.",
            "It’s best to call ahead for a same-day visit because walk-ins are limited.",
        ],
        bug="The agent should explicitly state the practice hours by day and avoid ambiguous statements about Saturday availability.",
        severity="Medium",
    ),
    CallScenario(
        key="call_05",
        title="Insurance verification",
        patient_goal="Ask if a new insurance plan is accepted and what to bring for a first visit.",
        patient_lines=[
            "I just switched insurance and want to know if the practice takes it.",
            "I also want to know what paperwork to bring on the first appointment.",
            "Can I upload the card before I come in?",
        ],
        agent_lines=[
            "I can check whether your plan is in-network, but I may need your member ID and group number.",
            "Please bring a photo ID, insurance card, and a list of current medications.",
            "Yes, you can upload your card through the patient portal or send a photo before the visit.",
        ],
        bug="The agent should not claim a plan is accepted without verifying the member plan and effective date.",
        severity="High",
    ),
    CallScenario(
        key="call_06",
        title="Cancelation with a reason",
        patient_goal="Cancel an appointment and ask whether there is a cancellation fee.",
        patient_lines=[
            "I need to cancel my appointment because I am sick.",
            "Do I have to pay a cancellation fee?",
            "Can I rebook after I recover?",
        ],
        agent_lines=[
            "I can cancel the visit. Please let me know the best day to reschedule once you are well.",
            "There is no fee for cancellations made more than 24 hours in advance, but same-day cancellations may be charged.",
            "I can place you on the waitlist for the next available slot after you recover.",
        ],
        bug="The agent must be accurate on policy wording and clearly distinguish between same-day and advance cancellations.",
        severity="Low",
    ),
    CallScenario(
        key="call_07",
        title="Weekend appointment edge case",
        patient_goal="Ask for a Sunday appointment and test office opening hours logic.",
        patient_lines=[
            "Can I come in Sunday at 10 am?",
            "I only have time on the weekend for this. Is there any office coverage?",
            "What is the next available weekday option?",
        ],
        agent_lines=[
            "I’ve scheduled you for Sunday at 10 am.",
            "I can check whether the office is open on the weekend, but it is typically closed.",
            "The next available weekday is Tuesday at 9:30 am if that works.",
        ],
        bug="Agent confirms Sunday booking without checking office-hours policy, which is a clear scheduling error.",
        severity="High",
    ),
    CallScenario(
        key="call_08",
        title="After-hours urgent concern",
        patient_goal="Ask what to do after hours for severe symptoms and whether to call emergency services.",
        patient_lines=[
            "I have severe chest pain and I am scared. What should I do right now?",
            "The office is closed now. Should I call 911 or wait for morning?",
            "What if I feel better by tomorrow?",
        ],
        agent_lines=[
            "Please call emergency services or go to the nearest urgent care right away. We cannot advise on chest pain over the phone.",
            "If the symptoms are severe or worsening, seek emergency care immediately rather than waiting.",
            "If you feel better tomorrow, still contact your primary care doctor as soon as possible.",
        ],
        bug="The bot must not use ambiguous language or downplay emergency risks in a pager or urgent-symptom conversation.",
        severity="Critical",
    ),
    CallScenario(
        key="call_09",
        title="Unclear patient request with interruptions",
        patient_goal="Ask for a refill while also discussing travel plans and interruptions from background noise.",
        patient_lines=[
            "I need a refill, but I am traveling next week and I am not sure when I can come in.",
            "Hold on, my kids are yelling in the background; can we do this later?",
            "I can still text the pharmacy if that is easier.",
        ],
        agent_lines=[
            "I can help. Please tell me the medication and pharmacy; I can start the refill process and note the travel issue.",
            "Let’s keep the line open and finish the key details before we end the call.",
            "I can send the refill request to the pharmacy and note that you may need a follow-up if the doctor has to review it.",
        ],
        bug="The agent should handle interruptions gracefully and ask for a concise summary before ending the call.",
        severity="Medium",
    ),
    CallScenario(
        key="call_10",
        title="Billing and copay question",
        patient_goal="Ask what the copay is and whether a visit can be split across two dates.",
        patient_lines=[
            "I want to know my copay before the visit and whether I can split an annual checkup over two dates.",
            "I also need to know if the office offers payment plans for a balance.",
            "I am not sure if my deductible has been met.",
        ],
        agent_lines=[
            "Your copay depends on your plan and the type of visit; I can look up the estimate after verifying coverage.",
            "The office does offer payment plans for balances after insurance processing, but the exact terms vary.",
            "I can help you review your deductible status once you share the insurance member ID.",
        ],
        bug="The agent should avoid making up payment plan or deductible details and should require verification before stating them as facts.",
        severity="Medium",
    ),
]


def find_scenario(name: str) -> CallScenario:
    for item in SCENARIOS:
        if item.key == name:
            return item
    raise ValueError(f"Scenario {name} not found")
