<!-- SPDX-License-Identifier: MIT -->

# Gate Contract

**Purpose:** Define what an agent builds for each step's gate. Gates are executable - they run within the protocol, validate, teach, and enable learning.

> HITL protocol and the MobileInterface-first rule live in
> `gate-contract-hitl.md`. Read that file too — both are mandatory.

---

## Gate Responsibilities

Every gate MUST do these 6 things:

| # | Action | Description |
|---|--------|-------------|
| 1 | **VALIDATE** | Check input data against criteria |
| 2 | **TEACH** | Record lesson on success or failure |
| 3 | **LEARN** | Send lesson to /kernel/learn for storage |
| 4 | **BLOCK** | Prevent next step if validation fails |
| 5 | **SAVE** | Persist state for next step |
| 6 | **LOOP** | Retry with teaching if recoverable failure |

---

## The Learning Cycle

```
Gate executes
    │
    ▼
VALIDATE ──► outcome (pass/fail)
    │
    ▼
TEACH ──► create lesson from outcome
    │
    ▼
LEARN ──► /kernel/learn stores lesson
    │
    ▼
Next execution ──► agent APPLIES stored lessons
    │
    ▼
Better validation ──► fewer failures ──► agent improves
```

---

## Gate Execution Flow

```
Protocol invokes gate
    │
    ▼
APPLY lessons (from previous runs)
    │
    ▼
VALIDATE input against criteria
    │
    ├── PASS ──► TEACH success ──► LEARN ──► SAVE state ──► PROCEED
    │
    └── FAIL ──► Can recover?
                    │
                    ├── YES ──► TEACH fix ──► LEARN ──► LOOP (retry)
                    │
                    └── NO ──► TEACH failure ──► LEARN ──► BLOCK ──► ESCALATE
```

---

## Gate Interface

Agent builds gates as skills/commands:

```
GATE: step_N_gate

INPUT:
  - data: {} (from previous step or user)
  - state: {} (accumulated workflow state)
  - lessons: [] (from /kernel/learn)

OUTPUT:
  - status: PASS | FAIL | RETRY
  - state: {} (updated state to save)
  - lesson: {} (to send to /kernel/learn)
  - next_action: PROCEED | LOOP | BLOCK | ESCALATE
```

---

## Evidence Gate (Mobile-Specific, Non-Negotiable)

In addition to the six responsibilities, the Step 4 gate enforces one more:

```
EVIDENCE:
  rule: every locator value written in this run appears verbatim in a
        page-source capture stored under tests/_state/captures/
  on_fail: BLOCK. Never downgrade to a warning, never "flag it in the report".
  teach: "an id that cannot be traced was reasoned about, not observed"
```

This gate cannot pass by producing a report that names the gap. It passes only
when the grep succeeds for every locator. A gate that emits a report and
proceeds is satisfied by any run that emits a report — which is to say, it
cannot fail, which is to say it is not a gate.

---

## Teaching Pattern

Gates create lessons:

```
LESSON:
  step: N
  signal: "What happened"
  outcome: "pass | fail | retry"
  insight: "What to learn"
  apply_when: "When to use this lesson"
```

Example:
```
LESSON:
  step: 4
  signal: "Every product tile in the catalog carried the id 'Product Name'"
  outcome: "fail"
  insight: "Repeated list items share one id; there is no per-item locator"
  apply_when: "Building a Screen Object for any list or grid screen"
```

---

## Learning Pattern

Gate sends lesson to /kernel/learn:

```
/kernel/learn receives lesson
    │
    ▼
Stores in domain knowledge
    │
    ▼
Next gate execution loads stored lessons
    │
    ▼
Gate APPLIES lessons before validating
```

Example application:
```
BEFORE (no lessons):
  - Gate asks "What test do you want to create?"
  - User says "test the login"
  - Gate fails (no persona)

AFTER (lesson applied):
  - Gate asks "What test? Format: 'As a [role], I want to [action]'"
  - User says "As a shopper, I want to sign in"
  - Gate passes
```

---

## Validation Criteria Pattern

```
CRITERIA:
  field_name:
    rule: "description of valid state"
    on_fail: "what to do if invalid"
    teach: "lesson to record"
```

---

## Loop Pattern

```
LOOP:
  max_retries: 3
  on_retry:
    - TEACH the fix
    - LEARN from failure
    - APPLY fix (if auto-fixable)
    - RE-VALIDATE
  on_max_retries:
    - TEACH escalation reason
    - LEARN from repeated failure
    - ESCALATE to user (HITL)
```

---

## State Persistence

```
STATE:
  location: "tests/_state/workflow_state.json"
  format:
    step: N
    status: "complete" | "failed" | "retry"
    data: {} (step output)

CAPTURES:
  location: "tests/_state/captures/{platform}-{screen-slug}.xml"
  rule: written in Step 4, never edited by hand, referenced by every locator

LESSONS:
  location: "domain lessons storage (via /kernel/learn)"
  format:
    step: N
    lessons: [] (accumulated insights)
```

---

## Building Gates During Domain-Setup

Agent reads workflow.md, then for each step:

1. **READ** step criteria from workflow.md
2. **LOAD** existing lessons from /kernel/learn
3. **BUILD** gate skill/command following this contract
4. **REGISTER** gate with protocol
5. **SAVE** gate to domain folder

---

## Gate Invocation in Protocol

```
/qa-workflow
    │
    ├── load lessons from /kernel/learn
    │
    ├── invoke step_1_gate(user_input, lessons)
    │       └── PASS ──► state saved, lesson sent to /kernel/learn
    │
    ├── invoke step_2_gate(state, lessons)
    │       └── PASS ──► state updated, lesson sent
    │
    └── ... continues through step 5
            │
            ▼
    workflow complete ──► all lessons stored ──► agent smarter next time
```

---

*Agent builds gates. Protocol runs gates. Gates teach. Agent learns. Agent improves.*
