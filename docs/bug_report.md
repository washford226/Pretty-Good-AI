# Bug Report

## 1) Potential Identity/Record-Matching Instability for Repeat Calls

- Severity: High
- Confidence: Medium (observed behavior is consistent, root cause is inferred)
- Summary: The agent appears to behave differently when caller identity details (name and/or date of birth) change between calls made from the same phone number.

### Observed Behavior

- In early test runs, changing name or date of birth for calls from the same number sometimes led to the agent refusing to proceed or moving toward transfer/escalation behavior.
- In later runs, using stable identity details produced more consistent flow.

### Why This Matters

- Real callers can make mistakes, correct themselves, or have shared-family phone lines.
- If identity matching is too brittle, legitimate users can be blocked from normal scheduling paths.

### Suspected Cause (Not Confirmed)

- The system may heavily rely on phone number as a primary identifier and may conflict with changing demographic fields (name/DOB), or may not gracefully handle repeat callers with updated details.

### Repro Steps

1. Place multiple calls from the same phone number.
2. In call A, provide one name/DOB combination.
3. In call B, provide a different name and/or DOB.
4. Compare outcomes (normal scheduling vs refusal/escalation/transfer behavior).

### Expected Behavior

- The agent should ask clarifying questions and continue safely, not fail hard or prematurely escalate.

---

## 2) Repeat-Appointment Handling With Same Caller Number

- Severity: Medium-High
- Confidence: High
- Summary: The agent can handle multiple appointments across separate calls, but requesting multiple appointments in a single call can trigger a failure path and transfer.

### Observed Behavior

- In the same call, after identity confirmation, the caller requested multiple appointments for the same day.
- The agent then failed to proceed and moved to transfer: "I can't proceed further right now... Transferring you now."
- This behavior was captured in call artifact: calls/9.json (call_sid: CAe086b14891bb702008ef0375a5c7e766).
- Across separate calls, creating appointments appears to work, so the issue is specifically tied to multi-appointment handling within one conversation.

### Why This Matters

- Real users sometimes book multiple visits in one interaction (follow-up scheduling, family coordination, or bundled requests).
- Failing mid-call after collecting identity creates poor UX and increases unnecessary transfer volume.

### Suspected Cause (Not Confirmed)

- Multi-appointment intent parsing or scheduling state management may not support more than one booking operation in the same dialogue state.
- The transfer fallback may trigger too aggressively when the booking workflow receives repeated same-day requests.

### Repro Steps

1. Start one call and complete identity verification (name, DOB, phone number).
2. Request multiple appointments for the same day in that same conversation.
3. Continue reaffirming the same request when prompted.
4. Observe the failure-to-proceed path followed by transfer.

### Expected Behavior

- The agent should either:
	- complete the multi-appointment request if policy allows, or
	- clearly explain constraints and offer alternatives (single booking + add-on flow, callback, or manual scheduling),
	without abruptly failing after successful identity verification.

---

## Notes

- Because backend data model and matching logic are not visible, these findings are framed as observed behavior + likely hypotheses rather than confirmed implementation defects.
- Relevant call artifacts for review are in the `calls/` directory (JSON transcripts and MP3 recordings).
