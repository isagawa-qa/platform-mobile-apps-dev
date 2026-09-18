<!-- SPDX-License-Identifier: MIT -->

# Step 4: Collaborative Construction (Capture, then Build)

**Purpose:** Discover elements from a live device session, then construct Screen/Task/Role/Test modules collaboratively.

**Workflow Version:** v4.0 (5-Step Pair Programming Workflow)

---

## A. Identity & Flow

| Field | Value |
|-------|-------|
| **Step** | 4 - Collaborative Construction |
| **Dependencies** | Step 3 complete (bdd_scenarios, expected_states, intent exist) |
| **Input** | State from Steps 1-3, a running Appium session |
| **Output** | `captures[]`, `discovered_elements`, Screen/Task/Role/Test files |

---

## B. Persona Map

| Persona | Actions |
|---------|---------|
| **User** | Watches the device or simulator, provides guidance on failures |
| **AI** | Drives the app, captures page source, constructs modules, validates |

---

## C. Discovery Phase (Capture-Driven)

A native app has no URL and no DOM. Discovery means driving the app to a screen
and dumping its accessibility tree, then reading ids out of that dump. The ids
are not guessable and are frequently not the visible label.

```
PRE-CHECK:
- Verify Step 3 complete
- READ credential_strategy from Step 2 state
- READ platform and device profile from Step 2 state

SESSION START:
- Create the session with `appium_session_management` (action=create). The app
  is launched by its capabilities. There is NO navigate step.
- The device must be on an INTERACTIVE venue. For a device not on this host,
  pass `remoteServerUrl`. CI cannot serve discovery - see step-02.md § I.
- IF the app needs a reset between runs, that is a capability
  (appium:noReset / appium:fullReset), never a test-level action.

CREDENTIAL HANDLING:
- IF none: proceed to capture
- IF static: load creds from tests/data/test_users.json, sign in
- IF dynamic: register a fresh user, save, sign in
- IF self-contained: register, sign in (do not persist)

PER SCREEN THE FLOW TOUCHES:
1. Drive the app to that screen, tapping only what the PREVIOUS dump revealed
2. `appium_get_page_source`, and write the XML to tests/_state/captures/
3. Extract candidate ids from the XML
4. Validate at least one actionable element was found
5. Record which capture each id came from

   Never tap by coordinate and never reuse an id from another app. The loop is
   the reusable part; the ids are per-app output. → steps/step-04-capture.md

CHECKPOINT:
- Every screen the BDD scenario names has a capture on disk
- Every locator you intend to write appears verbatim in one of them
- Block the construction phase until both hold
```

See `steps/step-04-capture.md` for the capture mechanics and id extraction.

---

## D. Construction Phase

### ⛔ BLOCKING GATE: Reuse Check Required (ALL THREE LAYERS)

**YOU CANNOT PROCEED TO D.4 WITHOUT COMPLETING THE REUSE CHECK.**

```
BEFORE writing ANY code, scan ALL THREE LAYERS:

1. RUN: find framework/screens -name "*.py" -not -name "__init__.py"
2. RUN: find framework/tasks   -name "*.py" -not -name "__init__.py"
3. RUN: find framework/roles   -name "*.py" -not -name "__init__.py"
4. SHOW: Display ALL output
5. CHECK: Look for same filename in different workflow folders (any layer)
6. IF DUPLICATE FOUND: Present HITL with consolidate options
7. WAIT: Get user decision before proceeding

❌ DO NOT skip any layer
❌ DO NOT assume no duplicates exist
❌ DO NOT proceed without showing scan results for ALL layers
```

**Commands:**
- `/qa-pre-construction` — Full checkpoint (includes reuse check)
- `/qa-reuse-check` — Standalone reuse check (if checkpoint was skipped)

**This gate blocks construction. No exceptions.**

---

### D.1 MANDATORY: Read Reference Files First

```
BEFORE writing ANY code:

1. READ reference files:
   - framework/_reference/screens/*.py → Screen Object patterns
   - framework/_reference/tasks/*.py   → Task patterns
   - framework/_reference/roles/*.py   → Role patterns
   - framework/_reference/tests/*.py   → Test patterns
   - framework/_reference/README.md    → Architecture + what differs from web

2. EXTRACT patterns:
   - Locator format (platform-keyed dicts, the locator() resolver)
   - Method signatures (return self, no returns, decorators)
   - Composition pattern (how layers connect)
   - Import paths

3. APPLY patterns to generated code
   - Match reference structure exactly
   - Use same decorator patterns
   - Follow same naming conventions

DO NOT skip this step. DO NOT rely on memory. READ the files.
```

### D.2 MANDATORY: MobileInterface Methods First

```
BEFORE writing ANY device interaction in a Screen Object:

1. READ framework/interfaces/mobile_interface.py
   - List all available methods
   - Understand what each does

2. FOR EACH interaction needed:
   - CHECK: Does MobileInterface already have this method?
   - IF YES: Use it directly
   - IF NO: STOP and ask user (see below)

3. NEVER write workarounds without asking:
   ❌ import time / time.sleep()
   ❌ Manual polling loops
   ❌ Direct Appium driver calls in a Screen Object
   ❌ Custom wait implementations
   ❌ Raw driver.find_element above the Interface layer

4. IF a MobileInterface method is missing, ASK USER:
   "Need MobileInterface method: [description]

   Use case: [what you're trying to do]
   Proposed signature: [method_name(params)]

   Options:
   1. Add this method to MobileInterface
   2. Use existing method [alternative] instead
   3. Other approach

   Which option?"

5. WAIT for user response before proceeding
```

### D.3 MANDATORY: Every Locator Traces To A Capture

```
FOR EACH locator you are about to write:

1. Take the literal string value
2. grep it against the captures recorded in C
3. IF NOT FOUND: you invented it. STOP. Do not write it.
4. Record which capture file and which platform it came from

Add a platform key ONLY for a platform you actually captured. A locator dict
with an "android" key and no Android capture is a claim about a device nobody
has looked at.
```

### D.4 Build Modules

**⛔ PREREQUISITE: /qa-pre-construction checkpoint MUST be complete before this section.**

```
AFTER completing /qa-pre-construction checkpoint (including reuse check):

BUILD SCREEN:
- Create screen class with discovered ids as platform-keyed locator constants
- Add a locator(self, name) resolver, exactly as the reference screens do
- Add atomic action methods (enter_*, tap_*, open_*)
- Add state-check methods from expected_states
- Use ONLY MobileInterface methods for interactions
- Return self from chainable actions
- NO decorators on a Screen Object
- Save to framework/screens/{workflow}/

BUILD TASK:
- Create task class composing the Screen Objects
- Add workflow method using Screen actions
- @autologger.automation_logger("Task") on methods, NONE on __init__
- NO locators in tasks
- NO direct driver calls - use Screen methods only
- NO return values
- Save to framework/tasks/{workflow}/

BUILD ROLE:
- Create role class composing the Task
- @autologger.automation_logger("Role Constructor") on __init__
- @autologger.automation_logger("Role") on workflow methods
- Workflow methods call MULTIPLE tasks
- NO return values
- Save to framework/roles/{workflow}/

BUILD TEST:
- Create test using the Role
- @pytest.mark.{platform} and @autologger.automation_logger("Test")
- AAA pattern (Arrange/Act/Assert)
- Assert via Screen state-check methods
- Test data: JSON files in tests/{workflow}/data/, read through the
  workflow_data fixture (tests/conftest.py) as
  workflow_data["<file name without .json>"]
- NO conftest.py in tests/{workflow}/ - shared fixtures live only
  in tests/conftest.py
- Save to tests/{workflow}/
```

---

## E-I. State, Teaching, Validation, HITL, Communication

State management, the teaching/learning signals, the validation criteria table,
the HITL discovery-failure protocol and the user-facing progress formats are in
`step-04-outcomes.md`. The validation criteria there are binding - read them
before declaring this step complete.

---

## Extended References

| Reference | Content |
|-----------|---------|
| `step-04-capture.md` | Capture mechanics, id extraction, platform keys |

---

*Next: Step 5 - Test Execution & HITL*
