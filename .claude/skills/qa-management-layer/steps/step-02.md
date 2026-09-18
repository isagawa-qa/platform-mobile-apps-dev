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
    locally, and conftest now blocks that combination with the alternatives
    named. Route it to a venue that reaches a machine which HAS the tooling -
    remote or cloud. NOT ci: see § I, ci cannot serve discovery.
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
| Host OS | `requires_host_os` must match the host | conftest BLOCKS with the alternatives; pick one (§ I) |
| Venue supports discovery | Must be an interactive venue, never `ci` | REPORT; offer `remote` or `cloud` (§ I) |
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

## I. Which Venue Can Do What

**Discovery and execution are different jobs and not every venue serves both.**
Discovery is a conversation with a device — look, decide, tap, look again.
Execution is a batch: run a suite that already exists and report.

| Venue | Device | Discovery (Step 4) | Execution (Step 5) |
|-------|--------|--------------------|--------------------|
| `local` | simulator/emulator or USB device on this host | **yes** — fastest | yes |
| `remote` | a machine on your network that has the tooling | **yes** — pass `remoteServerUrl` | yes |
| `cloud` | provider device farm | **yes** — pass `remoteServerUrl` | yes |
| `ci` | a fresh runner, per push | **no** | yes — this is its purpose |

**Why `ci` cannot do discovery.** A CI run is one shot: you commit a script, it
executes, you read the log. You cannot look at a screen and then decide what to
tap, because by the time you see anything the run is over. Scripting the walk
blind means tapping by coordinate, which misses — and you learn that ten minutes
later. Discovery needs a session you can hold open and interrogate.

**The cross-platform case, stated plainly.** iOS tooling exists only on macOS.
So for a non-macOS host:

| Your host | Target | Discovery venue |
|-----------|--------|-----------------|
| macOS | iOS | `local` |
| Windows / Linux | iOS | `remote` (a Mac you can reach) or `cloud` |
| any | Android | `local` |

The app artifact must be reachable from wherever the device is, not from where
you are sitting: a path on that machine for `remote`, an uploaded app reference
for `cloud`.

**Artifact kinds are not interchangeable**, and choosing the venue chooses the
artifact:

| Artifact | Runs on | Never on |
|----------|---------|----------|
| `.app` | a simulator | a real device |
| `.ipa` (signed) | a real device | a simulator |
| `.apk` | emulator **and** device | — |

A cloud farm of real iOS devices needs a signed `.ipa`. If the user has only a
simulator build, say so before they spend time on it.

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
