<!-- SPDX-License-Identifier: MIT -->

# Step 4 Payload: State, Validation and Outcomes

**Purpose:** What Step 4 records, what it must prove, and how it reports.

> Index: `step-04.md`

---

## E. State Management

| Field | Value |
|-------|-------|
| **State Saved** | `captures`, `discovered_elements`, `screen_path`, `task_path`, `role_path`, `test_path` |
| **When Saved** | After each module constructed |
| **State Location** | `tests/_state/workflow_state.json` |

```json
{
  "step": 4,
  "status": "complete",
  "data": {
    "captures": {
      "ProductCatalogScreen": "tests/_state/captures/ios-product-catalog.xml"
    },
    "discovered_screens": {
      "ProductCatalogScreen": {
        "platform": "ios",
        "elements": [
          { "constant": "SCREEN_ROOT", "by": "ACCESSIBILITY_ID",
            "value": "Catalog-screen", "capture": "ios-product-catalog.xml" }
        ]
      }
    },
    "files_created": [
      "framework/screens/catalog/product_catalog_screen.py",
      "framework/tasks/catalog/catalog_tasks.py",
      "framework/roles/catalog/shopper.py",
      "tests/catalog/test_browse_catalog.py"
    ]
  }
}
```

---

## F. Teaching & Learning

**What Agent Learns:**

| Signal | Lesson |
|--------|--------|
| Element not in the capture | The screen was not fully rendered when captured |
| Element appears only after a gesture | Capture after the gesture, not before |
| Every tile shares one id | Select by position or index, not by name |
| Id differs between platforms | The locator needs both keys, each from its own capture |
| Element found but not interactable | Check the context — it may be in a WEBVIEW |

**Lessons to Record:**
- Id patterns for this app
- Wait strategies that work
- Which locator strategies are stable on which platform

---

## G. Validation Criteria

| Phase | Rule | On Failure |
|-------|------|------------|
| Discovery | A capture exists for every named screen | AI drives to the screen, recaptures |
| Discovery | At least 1 actionable element per screen | AI re-prepares the screen, retries |
| Construction | Every locator traces to a capture | BLOCK — never write an invented id |
| Construction | Screen has locators | AI fixes module |
| Construction | Task has NO locators | AI fixes module |
| Construction | No driver call above the Interface | AI fixes module |

**Blocking Rule:** Cannot proceed to Step 5 until all modules valid.

---

## H. HITL Triggers

**When ANY failure occurs during discovery:**
1. **STOP** - Do not attempt autonomous fixes
2. **REPORT** - Show user exactly what failed
3. **WAIT** - Get human decision before proceeding

```
===== DISCOVERY FAILURE =====
What happened: [Specific failure]
Where: [screen, element, gesture]
Error: [Exact error message]

HOW SHOULD WE PROCEED?
1. AI Investigates - I analyze and propose fix
2. Provide Guidance - You tell me what you see on the device
3. Skip + Continue - Proceed without this element
4. Abort - Stop workflow entirely
```

---

## I. User Communication

**Discovery Progress:**
```
⚙ Step 4: Capturing screens...
  • Screen: ProductCatalogScreen
  • Platform: ios / iPhone 16 Pro 18.6
```

**Construction Progress:**
```
⚙ Step 4: Building Screen Object...
  • Screen: ProductCatalogScreen
  • Elements: 7 locators, all traced to ios-product-catalog.xml
```

**Complete:**
```
✓ Step 4: Collaborative Construction
  • Screen: ProductCatalogScreen (7 locators)
  • Task:   CatalogTasks.open_catalog()
  • Role:   Shopper.browse_catalog()
  • Test:   test_browse_catalog.py
```

---

---

*Return to `step-04.md`.*
