<!-- SPDX-License-Identifier: MIT -->

# Step 1: User Input

**Purpose:** Capture test requirement, persona, target app, and workflow identifier from user.

**Workflow Version:** v4.0 (5-Step Pair Programming Workflow)

---

## A. Identity & Flow

| Field | Value |
|-------|-------|
| **Step** | 1 - User Input |
| **Dependencies** | None (first step) |
| **Input** | User describes test requirement |
| **Output** | `persona`, `app`, `role_name`, `workflow`, `raw_requirement`, `detected_platform` |

---

## B. Persona Map

| Persona | Actions |
|---------|---------|
| **User** | Describes test requirement (persona, action, app) |
| **AI** | Asks questions, extracts data, resolves the platform, validates, saves state |

---

## C. Skill Instruction

```
PRE-CHECK:
- Clear session marker if starting a NEW workflow (not a retry)
  - If tests/_state/.current_run_id exists and the previous workflow
    completed Step 1 → delete marker

ACTION:
- ASK user: "What test do you want to create?"
  Format: "As a [persona], I want to [action]"
  Example: "As a shopper, I want to add a product to my cart"

- ASK user: "Which app?"
  Explanation: "An entry under `apps` in
  framework/resources/config/environment_config.json — e.g. demo_native."
  There is NO URL: a native app is launched by the session's capabilities.

- ASK user: "Which platform?"
  Options come from `platforms` in environment_config.json:
    ios | android | ios-web | android-web
  Explanation: "-web variants drive a mobile browser instead of an app."

- ASK user: "Workflow identifier?"
  Explanation: "Creates folders at framework/screens/{workflow}/ and
  tests/{workflow}/"

- EXTRACT from requirement:
  - persona: From "As a [X]" pattern
  - role_name: PascalCase conversion (shopper → Shopper)
  - raw_requirement: Full user requirement verbatim

- RESOLVE the platform entry:
  - Look up the chosen platform in environment_config.json → `platforms`
  - Read its `device_location` (may be an ${ENV:-default} expression — expand it)
  - Read `markers`, `family`, `default_app`
  - If the chosen app is not under `apps` → ASK user to add it

VALIDATE (see Section F):
- All required fields present and valid
- Save state on validation pass
- Block Step 2 until validation passes

CROSS-WORKFLOW DUPLICATE CHECK (after workflow identified):
- RUN: find framework/screens -name "*.py" -not -name "__init__.py"
- RUN: find framework/tasks   -name "*.py" -not -name "__init__.py"
- RUN: find framework/roles   -name "*.py" -not -name "__init__.py"
- CHECK: Same filename in different workflow folders = DUPLICATE
- IF DUPLICATE FOUND in ANY layer: Present HITL (see Section J)
- This runs ONCE per workflow, not per test

RETRY:
- If validation FAIL: RE-ASK the invalid/missing field
- No max retries (user provides input)
```

---

## D. State Management

| Field | Value |
|-------|-------|
| **State Saved** | `persona`, `app`, `role_name`, `workflow`, `raw_requirement`, `detected_platform` |
| **When Saved** | After validation passes |
| **State Location** | `tests/_state/workflow_state.json` |

```json
{
  "step": 1,
  "status": "complete",
  "data": {
    "persona": "shopper",
    "app": "demo_native",
    "role_name": "Shopper",
    "workflow": "catalog",
    "raw_requirement": "As a shopper, I want to add a product to my cart",
    "detected_platform": "ios",
    "device_location": "ci",
    "markers": ["ios"]
  }
}
```

---

## E. Teaching & Learning

**What Agent Learns:**

| Signal | Lesson |
|--------|--------|
| User provides incomplete persona | Re-ask with example format - users need guidance |
| App not in environment_config.json | Opportunity to expand the app registry |
| Workflow name conflicts with existing | Check existing structure before creating new |
| User names a URL | Remind: native apps launch by capability, not address |

**Lessons to Record:**
- Common persona patterns for this app
- Which platform the team defaults to
- Workflow naming conventions that work

---

## F. Validation Criteria

| Field | Rule | On Failure |
|-------|------|------------|
| `persona` | Must be present, from "As a [X]" pattern | RE-ASK with example |
| `app` | Must be a key under `apps` in environment_config.json | RE-ASK or offer to add |
| `detected_platform` | Must be a key under `platforms` | RE-ASK with the four options |
| `role_name` | Must be PascalCase conversion | Auto-fix from persona |
| `workflow` | Alphanumeric + hyphen/underscore | RE-ASK with examples |

**Blocking Rule:** Cannot proceed to Step 2 until all fields valid.

---

## G. Error Handling

| Issue | Behavior |
|-------|----------|
| User skips persona | RE-ASK: "I need a persona. Example: 'As a shopper, I want to...'" |
| User gives a URL | EXPLAIN: "A native app has no URL. Which app entry should I launch?" |
| Unknown app | ASK: "'{app}' is not in environment_config.json. Add it? (yes/no)" |
| Unknown platform | RE-ASK: "Choose one: ios, android, ios-web, android-web" |
| Missing workflow | RE-ASK: "What workflow identifier? (e.g., catalog, checkout-v2)" |

---

## H. Platform Resolution

1. Read `platforms` from `framework/resources/config/environment_config.json`
2. Select the entry the user named; if none, fall back to `default_platform`
3. Expand its `device_location` expression (`${MOBILE_DEVICE_LOCATION_IOS:-local}` → `local` unless set)
4. Record `family`, `markers` and `default_app` into state — Step 4 needs the
   markers to decorate the generated test, and Step 2 needs the device location

---

## I. User Communication

**Output Format:**
```
✓ Step 1: User Input
  • Persona: shopper
  • Role: Shopper
  • App: demo_native
  • Platform: ios (device_location: ci, markers: ios)
  • Workflow: catalog
```

---

## Flow Diagram

```
  User describes requirement
      │
      ▼
  AI extracts persona, asks for app, platform, workflow
      │
      ▼
  Resolve platform entry + device_location
      │
      ▼
  Validate all fields
      │
  ┌───┴───┐
  ▼       ▼
PASS    FAIL → RE-ASK
  │
  ▼
State saved → STEP 2
```

---

## J. Cross-Workflow Duplicate Check

**When:** After workflow is identified, before proceeding to Step 2.

**Scan all three layers:**
```bash
find framework/screens -name "*.py" -not -name "__init__.py"
find framework/tasks   -name "*.py" -not -name "__init__.py"
find framework/roles   -name "*.py" -not -name "__init__.py"
```

**Check for duplicates:** Same filename in different workflow folders.

**If duplicates found, present HITL:**

```
CROSS-WORKFLOW DUPLICATES DETECTED
==================================

Layer: Screens
  tab_bar_screen.py exists in:
    → framework/screens/catalog/tab_bar_screen.py
    → framework/screens/checkout/tab_bar_screen.py

Layer: Tasks
  (none found)

Layer: Roles
  (none found)

Generic modules should be consolidated to common/ folders.

OPTIONS:
1. CONSOLIDATE NOW - Move duplicates to common/, update all imports
2. CONTINUE - Proceed with workflow, consolidate later (technical debt)

Which option? (1/2):
```

**If user chooses CONSOLIDATE:**
1. Create `framework/screens/common/`, `framework/tasks/common/`, `framework/roles/common/` as needed
2. Move duplicate module to common/ folder
3. Update ALL imports across ALL workflows
4. Delete the duplicates
5. Run tests to verify nothing broke

**Generic modules (should be in common/):**
- Screens: TabBarScreen, LoginScreen, NavigationDrawerScreen, SearchScreen
- Tasks: AuthTasks (sign in / sign out), NavigationTasks
- Roles: (typically workflow-specific, but shared auth roles could be common)

---

*Next: Step 2 - Pre-flight Configuration*
