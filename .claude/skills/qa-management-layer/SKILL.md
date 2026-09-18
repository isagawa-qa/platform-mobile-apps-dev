<!-- SPDX-License-Identifier: MIT -->

---
name: qa-management-layer
description: 5-step QA test generation workflow for native and hybrid mobile apps. Agent self-enforces validation, teaches on outcomes, learns via /kernel/learn. Use for mobile test automation from user stories.
---

# QA Management Layer

**Purpose:** Define the 5-step QA workflow. Agent reads this, then self-enforces validation while executing.

**Philosophy:** Self-build, self-improve, safety-first.

---

## How This Works

```
1. /kernel/anchor reads protocol
2. Protocol points to this skill
3. Agent reads workflow.md + gate-contract.md + steps/*.md
4. User invokes /qa-workflow
5. Agent executes 5 steps, self-enforcing validation per gate-contract
6. On failure: /kernel/learn captures lesson
7. On success: /kernel/complete
```

---

## Skill Structure

```
qa-management-layer/
├── SKILL.md              ← You are here (entry point)
├── workflow.md           ← 5-step index with data flow
├── gate-contract.md      ← Validation contract (index)
├── gate-contract-hitl.md ← HITL protocol + MobileInterface-first rule
├── checkpoints/
│   ├── pre-construction.md ← Blocking checkpoint before any code
│   ├── on-failure.md       ← Triage a failing test
│   └── propose-fix.md      ← Propose a fix for review
└── steps/
    ├── step-01.md        ← User Input criteria
    ├── step-02.md        ← Pre-flight criteria
    ├── step-03.md        ← AI Processing criteria
    ├── step-04.md         ← Construction criteria
    ├── step-04-capture.md ← Page-source capture and id extraction
    ├── step-04-outcomes.md ← Step 4 state, validation and reporting
    ├── step-05.md         ← Execution criteria
    └── step-05-triage.md  ← HITL triage protocol + failure map
```

---

## Reading Order

1. **workflow.md** - Understand the 5 steps and data flow
2. **gate-contract.md** - Understand validation contract
3. **steps/step-XX.md** - Read each step's criteria

---

## Running the Workflow

When user invokes `/qa-workflow`:

```
/kernel/anchor (reads protocol → points here)
    │
    ▼
FOR step 1 to 5:
    │
    READ step criteria from steps/step-XX.md
    │
    EXECUTE step actions
    │
    VALIDATE per gate-contract:
        ├── PASS ──► SAVE state ──► PROCEED
        ├── RETRY ──► LOOP (max 3, then HITL)
        └── FAIL ──► BLOCK ──► ESCALATE
    │
    TEACH lesson (success or failure)
    │
    LEARN (send to /kernel/learn)
    │
COMPLETE ──► /kernel/complete
```

---

## Gate Contract (Self-Enforcement)

Agent self-enforces validation at each step. No separate gate files - agent reads criteria and validates inline.

See `gate-contract.md` for:
- What to validate
- How to teach on outcomes
- When to loop vs block
- How to learn via /kernel/learn

---

## Key Principles

| Principle | Description |
|-----------|-------------|
| **Self-Enforce** | Agent validates per step criteria, no external gates |
| **Self-Improve** | Agent learns from outcomes via /kernel/learn |
| **Safety-First** | Block bad data, escalate to HITL when stuck |
| **Pair Programming** | User decides, agent executes - NEVER loop autonomously |

---

## CRITICAL RULES (Read First)

### 1. HITL is Mandatory (No Autonomous Fixing)

On ANY failure:
1. **STOP** - Do not attempt fixes
2. **REPORT** - Show user what failed
3. **WAIT** - Get user decision
4. **ONLY THEN** proceed based on user choice

❌ NEVER loop through multiple fix attempts
❌ NEVER try "one more thing" without asking
❌ NEVER assume user wants you to fix it

See `gate-contract-hitl.md` → HITL Protocol section.

### 2. Read Reference Files Before Writing Code

Before Step 4 (Construction):
1. READ `framework/_reference/screens/*.py`
2. READ `framework/_reference/tasks/*.py`
3. READ `framework/_reference/roles/*.py`
4. READ `framework/_reference/tests/*.py`
5. EXTRACT patterns, APPLY to generated code

❌ NEVER write code from memory alone
❌ NEVER skip reading references

See `steps/step-04.md` → Section D.1.

### 3. MobileInterface Methods First

Before writing ANY device interaction:
1. CHECK if MobileInterface has the method
2. IF YES: Use it directly
3. IF NO: ASK user before creating workaround

❌ NEVER use time.sleep() in Screen Objects
❌ NEVER write manual polling loops
❌ NEVER call the Appium driver directly above the Interface
❌ NEVER create workarounds without asking

See `gate-contract-hitl.md` → MobileInterface Methods First section.

### 4. Never Type An Element Id From Memory

Every locator value MUST appear verbatim in a page source captured from a live
session during Step 4. A native app's accessibility ids are not guessable and
are not the same as the visible label.

❌ NEVER copy ids from a third-party repo or a tutorial
❌ NEVER infer an id from the on-screen text
❌ NEVER write a locator before its capture exists

See `steps/step-04-capture.md`.

---

## Mobile-Specific Rules

| Rule | Why |
|------|-----|
| No URL, no navigate step | A native app is launched by the session's capabilities |
| Locators are platform-keyed dicts | The same screen carries different ids on iOS and Android |
| `ACCESSIBILITY_ID` first | Stable across both platforms; XPath is a last resort |
| Only add a platform key you captured | An uncaptured key asserts an id on a platform nobody looked at |
| Check the context before a web assertion | Hybrid apps need `WEBVIEW_*`; native assertions run in `NATIVE_APP` |

---

## Entry Points

| Command | Description |
|---------|-------------|
| `/qa-workflow` | Run 5-step workflow (production) |
| `/qa-workflow-dev` | Run with dev permissions |
| `/qa-pre-construction` | Blocking checkpoint before Step 4 construction |
| `/qa-reuse-check` | Standalone reuse check |

---

## References

| File | Purpose |
|------|---------|
| `workflow.md` | 5-step index, data flow |
| `gate-contract.md` | Validation contract |
| `steps/*.md` | Step-specific criteria |

---

*Agent reads. Agent executes. Agent validates. Agent learns.*
