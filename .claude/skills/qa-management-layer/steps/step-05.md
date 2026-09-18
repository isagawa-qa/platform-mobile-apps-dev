<!-- SPDX-License-Identifier: MIT -->

# Step 5: Test Execution & HITL Iteration

**Purpose:** Execute test, validate results with HITL triage for failures, iterate through pair programming loop.

**Workflow Version:** v4.0 (5-Step Pair Programming Workflow)

---

## A. Identity & Flow

| Field | Value |
|-------|-------|
| **Step** | 5 - Test Execution & HITL Iteration |
| **Dependencies** | Step 4 complete (all modules generated and saved) |
| **Input** | Test files from Step 4, workflow state |
| **Output** | Test execution result, HITL triage decisions (if failure) |

---

## B. Persona Map

| Persona | Actions |
|---------|---------|
| **User** | Reviews results, makes triage decisions on failures |
| **AI** | Executes test, analyzes results, presents triage options |

---

## C. Skill Instruction

```
PRE-CHECK:
- Verify Step 4 complete (all files saved)
- Verify test file path exists
- Verify the device is still reachable — a simulator that died between
  Step 4 and Step 5 produces a session error that looks like a code defect

ACTION (2-STEP SEQUENCE):
1. EXECUTE pytest via Bash:
   - Command: python -m pytest {test_path} -m {marker} --platform={platform} -v
   - The marker and platform come from Step 1 state, never from memory
   - Capture exit code and output
   - Construct test_result:
     {
       "status": "passed" | "failed" | "crashed",
       "exit_code": <exit_code>,
       "output": <stdout + stderr>,
       "duration": <execution time>,
       "failure_data": <parse from output if failed>
     }

   Exit code 5 means NOTHING WAS COLLECTED, not that the test passed.
   Treat it as a failure of the generation step: the file is in the wrong
   place, or its marker does not match -m, or its class/function naming
   does not match pytest.ini's discovery patterns.

2. VALIDATE test_result:
   - IF passed -> WORKFLOW COMPLETE
   - IF failed -> HITL triage workflow

HITL TRIAGE OPTIONS (on test failure):
1. Application Defect - Log defect, block workflow
2. Test Issue - AI proposes a fix, user approves, retry
3. Investigate - Show full diagnostic data
4. Other - User describes action

RETRY POLICY:
- Error signature tracking (hash of the normalized error)
- Max 2 retries per unique error signature
- Flaky test detection (passes after retry)

COMPLETION CRITERIA:
- ONLY mark Step 5 complete if test passes
- DO NOT mark complete on failure
- Workflow status "AWAITING TRIAGE" until test passes
```

---

## D. State Management

| Field | Value |
|-------|-------|
| **State Saved** | `test_result`, `triage_decision`, `retry_count` |
| **When Saved** | After test execution |
| **State Location** | `tests/_state/workflow_state.json` |

**Pass State:**
```json
{
  "step": 5, "status": "complete",
  "data": {
    "test_result": {"status": "passed", "exit_code": 0, "duration": 18.4},
    "triage_decision": null,
    "retry_count": 0
  }
}
```

**Failure State:**
```json
{
  "step": 5, "status": "awaiting_triage",
  "data": {
    "test_result": {"status": "failed", "exit_code": 1, "failure_data": {...}},
    "diagnostic_data": {...},
    "ai_analysis": {"likely_cause": "...", "confidence": 75}
  }
}
```

---

## E. Teaching & Learning

**What Agent Learns:**

| Signal | Lesson |
|--------|--------|
| Test passes first time | Construction phase produced valid code |
| Element not found | The capture is stale, or the app is in another context |
| Assertion failed | Expected state doesn't match actual |
| Timeout error | Element wait needs adjustment, or the screen never rendered |
| Session died mid-test | Device or Appium instability, not a code defect |
| Same error twice | This isn't flaky - need a real fix |

**Lessons to Record:**
- Common failure patterns for this app
- Effective triage decisions
- Fixes that worked

---

## F. Validation Criteria

| Check | Rule | On Failure |
|-------|------|------------|
| `test_result.status` | Must be passed/failed/crashed | Report error |
| `test_result.exit_code` | Must be present | Report error |
| Exit code 5 | Nothing collected — a generation defect | Fix path/marker/naming |
| Test passes | status == "passed" | Trigger HITL triage |

**Blocking Rule:** Workflow cannot complete until test passes.

---

## G. HITL Triage Protocol (MANDATORY - NO AUTONOMOUS FIXES)

**CRITICAL: Agent MUST stop and ask on EVERY failure. No exceptions.**

The full protocol — the failure report format, the five triage options, what
"AI Proposes Fix" means, the forbidden behaviours and the retry policy — is in
`step-05-triage.md` § HITL Triage Protocol. Read it before responding to any
failure.

**CHECKPOINT:** On ANY failure, invoke `/qa-on-failure` FIRST.

---

## H. Diagnostic Data

See `step-05-triage.md` for the diagnostic types and the mobile failure map.

**Quick Reference:**
1. Error message and stack trace
2. Screenshot at failure point (conftest captures this)
3. Page source at failure point
4. Current context and the full context list
5. Element state (displayed, enabled)
6. Device and session facts
7. Timing data

---

## I. User Communication

**In Progress:**
```
⚙ Step 5: Executing Test...
  • Test: tests/catalog/test_browse_catalog.py
  • Device: iPhone 16 Pro / iOS 18.6 (visible)
```

**Complete (Passed):**
```
✓ Step 5: Test Execution
  • Status: PASSED
  • Duration: 18.4s

5-Step QA Workflow Complete!
```

**Failed (Awaiting Triage):**
```
✗ Step 5: Test Execution - FAILED (Awaiting Triage)
  • Assertion: is_add_to_cart_available() returned False
  • Next: Choose (1: App Defect, 2: Propose Fix, 3: Investigate)
  • Workflow Status: INCOMPLETE
```

---

## Flow Diagram

```
  Verify Step 4 complete + device reachable
      │
      ▼
  Execute pytest via Bash
      │
      ▼
  Construct test_result
      │
      ▼
  Validate result
      │
  ┌───┴───────────┐
  ▼               ▼
PASSED        FAILED
  │               │
  │               ▼
  │         HITL TRIAGE
  │               │
  │         ┌─────┴─────┬─────────┐
  │         ▼           ▼         ▼
  │    Propose Fix  App Defect  Investigate
  │         │           │         │
  │         ▼           ▼         ▼
  │    User approves  Log + STOP  Show data
  │    + retry
  │         │
  └─────────┘
      │
      ▼
 WORKFLOW COMPLETE
```

---

## Extended References

| Reference | Content |
|-----------|---------|
| `step-05-triage.md` | Diagnostic types + the mobile failure map |

---

*Step 5 completes the 5-Step QA Workflow.*
