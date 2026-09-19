---
description: Start 5-step QA test generation workflow for mobile (Production mode - restricted permissions)
---

# QA Test Generation Workflow (Production)

You are starting the 5-step QA test generation workflow with collaborative construction.

## Kernel Loop Integration

1. **Do NOT invoke `/kernel/anchor` here.** Anchoring is hook-driven, not a
   workflow concern: `universal-gate-enforcer.py` blocks when `anchored` is
   false and again past the action limit, and `/kernel/session-start` sets
   `anchored: false` on a fresh session precisely so the hook forces one.
   Anchor when the hook asks, with the token it issues - never on entry,
   which spends actions on a re-centre the counter did not ask for.
2. **On failure:** Invoke `/kernel/fix` then `/kernel/learn` after any fix
3. **On completion:** Invoke `/kernel/complete` when workflow finishes

## Instructions

**⛔ MANDATORY: Read step files EVERY TIME this command is invoked.**

1. **Read ALL of these files NOW (use Read tool — NO EXCEPTIONS, NO SKIPPING):**
   ```
   .claude/skills/qa-management-layer/SKILL.md
   .claude/skills/qa-management-layer/steps/step-01.md
   .claude/skills/qa-management-layer/steps/step-04.md
   .claude/skills/qa-management-layer/steps/step-04-capture.md
   .claude/skills/qa-management-layer/checkpoints/pre-construction.md
   .claude/lessons/lessons.md
   ```

   **DO NOT skip because "already read this session".**
   **DO NOT rely on memory from previous workflows.**
   **READ THEM EVERY TIME.**

   `lessons.md` is created by `/kernel/domain-setup`. If this repo has not been
   through domain-setup, note that it is absent and continue — do not create it.

   **After reading, confirm:** "All protocol files read (including lessons)."

2. **THEN prompt user for requirement:**

   Ask the user:
   ```
   What test do you want to generate?

   Please provide:
   - Persona — e.g., "guest", "shopper", "admin"
   - App — an entry under `apps` in
     framework/resources/config/environment_config.json (e.g. demo_native)
   - Platform — ios | android | ios-web | android-web
   - What you want to do — e.g., "add a product to the cart"
   - Workflow identifier — creates folders at framework/screens/{workflow}/
     and tests/{workflow}/

   Format: "As a [persona], I want to [action] in [app] on [platform]"

   Example: "As a shopper, I want to add a product to the cart in demo_native on ios"
   ```

   **There is no URL.** A native app is launched by the session's capabilities.
   If the user gives a URL, they want a `-web` platform — confirm which.

3. **Execute the 5-step workflow:**
   - Step 1: User Input + Cross-workflow duplicate check (see step-01.md Section J)
   - Step 2: Pre-flight Configuration (device reachable, credential strategy)
   - Step 3: AI Processing (BDD, expected states, screens touched)
   - Step 4: Capture + Construction (includes /qa-pre-construction checkpoint)
   - Step 5: Test Execution

---

## CRITICAL: Production Mode Restrictions

**You are in PRODUCTION mode. The following restrictions apply:**

### You CAN generate/modify:
- `tests/` - Test files
- `framework/screens/` - Screen object files
- `framework/tasks/` - Task files
- `framework/roles/` - Role files
- `tests/data/` - Test data files

### You CANNOT modify:
- `.claude/skills/` - Skill files
- `.claude/commands/` - Command files
- `framework/interfaces/` - MobileInterface
- `framework/resources/` - Core utilities and config
- `framework/_reference/` - The reference implementation
- `CLAUDE.md` - Configuration files

### On Failure Behavior:

If a quality gate fails or a tool produces an error:

1. **STOP** - Do not attempt to fix framework code
2. **REPORT** - Show the user:
   ```
   Workflow stopped due to an issue.

   Step: [step number]
   Error: [error message]

   This appears to be a framework issue. Please contact support or report at:
   https://github.com/[repo]/issues
   ```
3. **DO NOT** attempt to modify any files in the restricted list above
4. **DO NOT** retry with workarounds that modify framework internals

---

Do NOT proceed to Step 2 until user provides their requirement.
