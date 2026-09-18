<!-- SPDX-License-Identifier: MIT -->

# Step 2: Pre-flight Configuration

**Purpose:** Establish credential strategy and confirm a device is reachable before test construction begins.

**Workflow Version:** v4.0 (5-Step Pair Programming Workflow)

---

## A. Identity & Flow

| Field | Value |
|-------|-------|
| **Step** | 2 - Pre-flight Configuration |
| **Dependencies** | Step 1 complete |
| **Input** | Step 1 output (persona, app, platform, workflow) |
| **Output** | `credential_strategy`, `device_profile` |

---

## B. Persona Map

| Persona | Actions |
|---------|---------|
| **User** | Answers credential question, starts a device if none is running |
| **AI** | Asks question, checks the device, validates, scaffolds if needed, saves state |

---

## C. Skill Instruction

```
PRE-CHECK:
- Verify Step 1 complete (persona, app, platform, workflow exist in state)
- Verify a device is reachable for the chosen platform and venue:
    local/ci  → the Appium server answers at server_url, and a simulator or
                emulator is booted
    remote    → the device's Appium server answers
    cloud     → credentials for the cloud provider are present in the env
- Verify the host OS can run the platform:
    ios requires_host_os = darwin. A Windows or Linux host CANNOT run iOS
    locally. Route it to the ci or cloud venue instead of failing.
- Verify the app artifact exists at the resolved path, or that the cloud
  app id is set

ACTION:
- ASK user: Credential strategy?
  1. Static         - Use existing account from tests/data/test_users.json
  2. Dynamic        - Register fresh user, save for later tests
  3. Self-contained - Register and use within same test
  4. None needed    - Test doesn't require credentials

DEFAULTS (no questions):
- Device: whatever the resolved venue provides; never headless — a simulator
  or emulator window is visible so the user can watch discovery happen
- Test data: Workflow-specific (tests/{workflow}/data/), loaded by the
  workflow_data fixture

VALIDATE (see Section E):
- Credential strategy must be a valid option
- A device must be reachable
- Save state on validation pass
- Scaffold infrastructure if needed

RETRY:
- If validation FAIL: RE-ASK credential question, or report the device
  problem and WAIT — do not silently switch venue
```

---

## D. State Management

| Field | Value |
|-------|-------|
| **State Saved** | `credential_strategy`, `device_profile` |
| **When Saved** | After validation passes |
| **State Location** | `tests/_state/workflow_state.json` |

```json
{
  "step": 2,
  "status": "complete",
  "data": {
    "credential_strategy": "static | dynamic | self-contained | none",
    "device_profile": {
      "platform": "ios",
      "venue": "ci",
      "server_url": "http://127.0.0.1:4723",
      "device_name": "iPhone 16 Pro",
      "platform_version": "18.6"
    }
  }
}
```

---

## E. Validation Criteria

| Field | Rule | On Failure |
|-------|------|------------|
| `credential_strategy` | Must be: static, dynamic, self-contained, none | RE-ASK |
| Appium server | Must answer at `server_url` | REPORT, wait for user |
| Device | A simulator/emulator/device must be booted | REPORT, wait for user |
| Host OS | `requires_host_os` must match, or venue must be ci/cloud | REPORT the venue options |
| App artifact | Path exists, or cloud app id set | REPORT the resolved path |

**Blocking Rule:** Cannot proceed to Step 3 until credential strategy is valid
and a device is reachable.

---

## F. Teaching & Learning

**What Agent Learns:**

| Signal | Lesson |
|--------|--------|
| User chooses static | App has existing test accounts |
| User chooses dynamic | App needs a registration flow |
| User chooses self-contained | Test is independent |
| User chooses none | No auth required for this test |
| iOS requested on Windows | Route to ci; record that this host cannot run iOS locally |
| Appium not answering | Record the start command that worked, for next time |

---

## G. Infrastructure Scaffolding

| Strategy | Infrastructure Created |
|----------|----------------------|
| `static` or `dynamic` | `tests/data/test_users.json` if missing |
| `self-contained` or `none` | None needed |
| any | `tests/_state/captures/` for Step 4 |

---

## H. User Communication

**Output Format:**
```
✓ Step 2: Pre-flight
  • Credentials: static (use existing account)
  • Device: iPhone 16 Pro / iOS 18.6 (venue: ci)
  • Appium: http://127.0.0.1:4723 responding
```

---

## Flow Diagram

```
  Verify device reachable for platform + venue
      │
  ┌───┴───┐
  ▼       ▼
 OK    NOT OK → REPORT + WAIT (never switch venue silently)
  │
  ▼
  ASK credential strategy
      │
      ▼
  Validate answer
      │
  ┌───┴───────┐
  ▼           ▼
PASS        FAIL
  │           │
  ▼           ▼
Save      RE-ASK
  │
  ▼
STEP 3
```

---

*Next: Step 3 - AI Processing*
