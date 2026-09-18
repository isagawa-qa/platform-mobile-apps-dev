<!-- SPDX-License-Identifier: MIT -->

# Step 3: AI Processing

**Purpose:** Transform user requirement into structured metadata (BDD scenarios, expected states, intent).

**Workflow Version:** v4.0 (5-Step Pair Programming Workflow)

---

## A. Identity & Flow

| Field | Value |
|-------|-------|
| **Step** | 3 - AI Processing |
| **Dependencies** | Step 2 complete |
| **Input** | Step 1-2 state (persona, app, role_name, workflow, raw_requirement) |
| **Output** | `bdd_scenarios`, `expected_states`, `intent`, `screens_touched` |

---

## B. Persona Map

| Persona | Actions |
|---------|---------|
| **User** | None (unless AI fails 3 times, then user decides resolution) |
| **AI** | Creates BDD scenario, extracts expected_states, determines intent, names the screens, validates, saves state |

---

## C. Skill Instruction

```
PRE-CHECK:
- Verify Step 2 complete (persona, app, role_name, workflow exist in state)

ACTION:
- READ raw_requirement from state
- CREATE BDD scenario with Given/When/Then structure
- EXTRACT expected_states from "Then" clauses
- DETERMINE intent (action verb from requirement)
- NAME every screen the scenario touches → screens_touched

  screens_touched is what Step 4 captures. A screen that is not named here
  will not be captured, and a locator on it cannot be written. Walk the
  Given and every When clause and name the screen each one happens on.

VALIDATE (see Section F):
- BDD structure must be valid
- At least one expected_state
- Intent must be present
- At least one screen named
- Save state on validation pass

RETRY:
- If validation FAIL: AI retries processing (max 3 attempts)
- After 3 failures: STOP → REPORT → USER DECIDES

POST-ACTION:
- WRITE transcript entry to tests/_reports/<run_id>/workflow_transcript.md
```

---

## D. State Management

| Field | Value |
|-------|-------|
| **State Saved** | `bdd_scenarios`, `expected_states`, `intent`, `screens_touched` |
| **When Saved** | After validation passes |
| **State Location** | `tests/_state/workflow_state.json` |

```json
{
  "step": 3,
  "status": "complete",
  "data": {
    "bdd_scenarios": [
      {
        "given": "the app is launched and showing the catalog",
        "when": ["I open the first product", "I add it to the cart"],
        "then": ["the catalog should have rendered products",
                 "the product should be addable to the cart"]
      }
    ],
    "expected_states": ["product_count", "is_add_to_cart_available"],
    "intent": "add_to_cart",
    "screens_touched": ["ProductCatalogScreen", "ProductDetailScreen", "TabBarScreen"]
  }
}
```

---

## E. Teaching & Learning

**What Agent Learns:**

| Signal | Lesson |
|--------|--------|
| "Then" clause doesn't map to state method | Improve extraction pattern |
| Intent extraction fails | Requirement may need clarification |
| BDD scenario too complex | Consider splitting into multiple scenarios |
| A screen was missed until Step 4 | Walk every When clause, not just the first |
| 3 failures in a row | This requirement pattern needs user guidance |

**Lessons to Record:**
- BDD patterns that work for this app
- Common intent verbs for this workflow
- expected_state naming conventions

---

## F. Validation Criteria

| Field | Rule | On Failure |
|-------|------|------------|
| `bdd_scenarios` | Must have valid Given/When/Then | AI retries |
| `expected_states` | At least one state from "Then" | AI retries |
| `intent` | Action verb extracted | AI retries |
| `screens_touched` | At least one screen named | AI retries |

**Blocking Rule:** Cannot proceed to Step 4 until metadata complete.

---

## G. Error Handling

| Attempt | Behavior |
|---------|----------|
| 1-3 | Validation rejects → AI retries processing |
| After 3 | STOP → REPORT → USER DECIDES |

**Error Message Template (After 3 Failures):**
```
"I've attempted 3 times and cannot produce valid metadata.

Here's what I'm generating:
[show failing output]

Validation issue:
[show error]

How should we proceed?
1. Clarify requirement - Go back to Step 1
2. Abort workflow - Stop and log issue"
```

**Note:** No "proceed with incomplete" option. Incomplete data never propagates.

---

## H. BDD Scenario Format

```gherkin
Scenario: [Intent description]
  Given [precondition - which screen the app is on]
  When [action 1]
  And [action 2]
  Then [expected outcome 1]
  And [expected outcome 2]
```

The `Given` names a SCREEN, never a URL. A native app is launched by its
capabilities, so the precondition is "the app is showing X", not "I am at
https://…". If the requirement names a URL, the platform is a `-web` variant
and the Given should say which page the mobile browser is on.

**Expected States Extraction:**
- "the catalog should have rendered products" → `product_count`
- "the product should be addable" → `is_add_to_cart_available`
- "the cart badge should show 1" → `cart_badge_count`

Each expected_state becomes a state-check method on a Screen Object in Step 4.

---

## I. User Communication

**Output Format:**
```
✓ Step 3: AI Processing
  • Intent: add_to_cart
  • Scenarios: 1
  • Expected states: 2 (product_count, is_add_to_cart_available)
  • Screens to capture: 3 (ProductCatalogScreen, ProductDetailScreen, TabBarScreen)
```

---

## Flow Diagram

```
  Read raw_requirement from state
      │
      ▼
  AI creates BDD scenario
      │
      ▼
  Extract expected_states from "Then"
      │
      ▼
  Determine intent + name screens touched
      │
      ▼
  Validate metadata
      │
  ┌───┴───────────┐
  ▼               ▼
PASS          FAIL (retry)
  │               │
  │         ┌─────┴─────┐
  │         ▼           ▼
  │      Retry 1-3   After 3
  │         │           │
  │         │           ▼
  │         │     USER DECIDES
  │         │
  ▼         │
State saved ←┘
      │
      ▼
   STEP 4
```

---

*Next: Step 4 - Collaborative Construction*
