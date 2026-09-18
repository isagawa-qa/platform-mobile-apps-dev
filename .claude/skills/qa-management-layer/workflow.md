<!-- SPDX-License-Identifier: MIT -->

# QA Workflow (5-Step)

**Purpose:** Index of the 5-step QA workflow. Agent reads this to understand data flow and validation criteria.

---

## Workflow Overview

```
Step 1: User Input ──► persona, app, workflow
    │
    ▼ (validate, teach, save state)
Step 2: Pre-flight ──► credential_strategy, platform, device profile
    │
    ▼ (validate, teach, save state)
Step 3: AI Processing ──► bdd_scenarios, expected_states, intent
    │
    ▼ (validate, teach, save state)
Step 4: Construction ──► captured page source, Screen, Task, Role, Test files
    │
    ▼ (validate, teach, save state)
Step 5: Execution ──► test_result, HITL triage if failed
    │
    ▼ (validate, teach, learn)
COMPLETE ──► lessons stored via /kernel/learn
```

---

## Step Index

| Step | Purpose | Input | Output | Reference |
|------|---------|-------|--------|-----------|
| 1 | User Input | User requirement | persona, app, workflow, role_name | `steps/step-01.md` |
| 2 | Pre-flight | Step 1 state | credential_strategy, platform, device | `steps/step-02.md` |
| 3 | AI Processing | Steps 1-2 state | bdd_scenarios, expected_states, intent | `steps/step-03.md` |
| 4 | Construction | Steps 1-3 state + live session | elements, Screen, Task, Role, Test | `steps/step-04.md` |
| 5 | Execution | Step 4 files | test_result, triage_decision | `steps/step-05.md` |

---

## Data Flow

```
USER INPUT
    │
    └──► { persona, app, workflow, role_name, raw_requirement }
              │
              ▼
         PRE-FLIGHT
              │
              └──► { credential_strategy, platform, device_profile }
                        │
                        ▼
                   AI PROCESSING
                        │
                        └──► { bdd_scenarios, expected_states, intent }
                                  │
                                  ▼
                             CONSTRUCTION
                                  │
                                  └──► { captures[], discovered_elements, files_created[] }
                                            │
                                            ▼
                                       EXECUTION
                                            │
                                            └──► { test_result, lessons[] }
```

---

## Validation Per Step

Agent self-enforces validation at each step:

| Step | Validates | Teaches | On Failure |
|------|-----------|---------|------------|
| 1 | persona, app, workflow present | User input patterns | ASK user for missing info |
| 2 | credential_strategy + platform valid | Credential and device preferences | ASK user again |
| 3 | bdd_scenarios, expected_states, intent present | BDD extraction patterns | STOP, ask user |
| 4 | page source captured, ids traced, files created | Construction patterns | STOP, ask user |
| 5 | test passes | Failure patterns, fixes | STOP, HITL triage |

**CRITICAL: On ANY failure, agent STOPS and asks user. No autonomous looping.**

---

## Mandatory Pre-Construction (Step 4)

Before writing ANY code in Step 4:

```
1. READ reference files:
   - framework/_reference/screens/*.py
   - framework/_reference/tasks/*.py
   - framework/_reference/roles/*.py
   - framework/_reference/tests/*.py
   - framework/_reference/README.md

2. READ MobileInterface:
   - framework/interfaces/mobile_interface.py
   - Use existing methods, ask before creating new ones

3. CAPTURE the page source for every screen the flow touches
   - No locator is written before its capture exists

4. ONLY THEN write code following reference patterns
```

**DO NOT skip these reads. DO NOT write from memory.**

---

## State Location

All steps save state to: `tests/_state/workflow_state.json`

```json
{
  "current_step": 3,
  "steps": {
    "1": { "status": "complete", "data": {...} },
    "2": { "status": "complete", "data": {...} },
    "3": { "status": "in_progress", "data": {...} }
  }
}
```

Captured page sources are written beside it, under `tests/_state/captures/`.

---

## Where Generated Code Lands

| Layer | Path |
|-------|------|
| Screen | `framework/screens/{workflow}/` |
| Task | `framework/tasks/{workflow}/` |
| Role | `framework/roles/{workflow}/` |
| Test | `tests/{workflow}/` |
| Test data | `tests/{workflow}/data/*.json`, read via the `workflow_data` fixture |

`tests/` ships with `conftest.py` and `data/` only. Generated suites create their
own `tests/{workflow}/` folder. There is never a second `conftest.py` — shared
fixtures live only in `tests/conftest.py`.

---

## Learning Flow

```
Each step:
    │
    ├── VALIDATES ──► creates lesson
    │
    ├── TEACHES ──► sends to /kernel/learn
    │
    └── LEARNS ──► applies lessons next run

Lessons accumulate ──► agent improves ──► fewer failures
```

---

## Protocol Execution

When user invokes `/qa-workflow`:

```
/kernel/anchor (reads protocol)
    │
    ▼
Protocol points to this skill
    │
    ▼
Agent reads workflow.md + gate-contract.md
    │
    ▼
FOR step 1 to 5:
    │
    ├── READ criteria from steps/step-XX.md
    │
    ├── EXECUTE step actions
    │
    ├── VALIDATE per gate-contract
    │       ├── PASS: save state, continue
    │       ├── RETRY: loop with teaching
    │       └── FAIL: block, escalate to HITL
    │
    ├── TEACH lesson
    │
    └── LEARN via /kernel/learn
    │
/kernel/complete
```

---

*Read step files for detailed criteria. See gate-contract.md for validation rules.*
