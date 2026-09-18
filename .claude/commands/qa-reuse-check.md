---
description: Scan for duplicate modules and present consolidation options (HITL)
---

# /qa-reuse-check

**Purpose:** Force a reuse check scan before construction phase.

## Instructions

**1. RUN ALL THREE COMMANDS and SHOW output:**

```bash
find framework/screens -name "*.py" -not -name "__init__.py"
find framework/tasks   -name "*.py" -not -name "__init__.py"
find framework/roles   -name "*.py" -not -name "__init__.py"
```

`framework/screens/` is the mobile Screen Object layer — the equivalent of a web
platform's `pages/`. If a directory does not exist yet, say so explicitly; an
empty result from a missing directory is not evidence of no duplicates.

**2. ANALYZE each layer for duplicates:**

Look for the SAME filename appearing in DIFFERENT workflow folders:
- `tab_bar_screen.py` in `catalog/` AND `checkout/` → DUPLICATE
- `auth_tasks.py` in multiple workflows → DUPLICATE
- `product_catalog_screen.py` only in `catalog/` → NOT a duplicate (workflow-specific)

**3. IF any duplicates found in ANY layer, PRESENT this to user:**

```
DUPLICATE MODULES FOUND
=======================

SCREENS:
  tab_bar_screen.py exists in:
    → framework/screens/catalog/tab_bar_screen.py
    → framework/screens/checkout/tab_bar_screen.py

TASKS:
  auth_tasks.py exists in:
    → framework/tasks/catalog/auth_tasks.py
    → framework/tasks/checkout/auth_tasks.py

ROLES:
  (none found)

This violates DRY. Generic modules should be consolidated.

OPTIONS:
1. CONSOLIDATE NOW - Move ALL duplicates to common/, update imports
2. SKIP FOR NOW - Continue, consolidate later

Which option? (1/2):
```

**4. WAIT for user response before proceeding.**

**5. If CONSOLIDATE chosen:**
- Create `framework/screens/common/`, `framework/tasks/common/`, `framework/roles/common/` as needed
- Move the modules there
- Update imports in ALL files that used the old paths
- Delete the duplicates
- Run tests to verify nothing broke

**Consolidating a Screen Object merges its locator dicts too.** Two copies can
carry different platform keys — one captured on iOS, one on Android. Keep every
key that has a capture behind it; drop none silently.

## Generic vs Workflow-Specific

**Generic (should be in common/):**
- Screens: TabBarScreen, LoginScreen, NavigationDrawerScreen, SearchScreen
- Tasks: AuthTasks, NavigationTasks (sign in / sign out flows)
- Roles: Shared authentication roles

**Workflow-specific (keep in workflow folder):**
- Screens: ProductCatalogScreen, ProductDetailScreen, CheckoutInfoScreen
- Tasks: ShoppingTasks, CheckoutTasks
- Roles: Domain-specific user personas

## When to Use

Invoke `/qa-reuse-check` if:
- Starting a new workflow that might reuse existing modules
- Pre-construction checkpoint was skipped
- You suspect duplicates exist but weren't checked
