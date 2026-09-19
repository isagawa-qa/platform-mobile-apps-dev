---
description: Start 5-step QA test generation workflow for mobile (Development mode - full access with approval)
---

# QA Test Generation Workflow (Development)

You are starting the 5-step QA test generation workflow in **DEVELOPMENT** mode with collaborative construction.

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

## Development Mode Permissions

**You are in DEVELOPMENT mode. Full access granted WITH USER APPROVAL.**

### You CAN modify (with user approval):
- `tests/` - Test files
- `framework/` - All framework code (screens, tasks, roles, interfaces)
- `.claude/skills/` - Skill files
- `.claude/commands/` - Command files
- `docs/` - Documentation

### CRITICAL: Approval Required for ALL Changes

**Before modifying ANY file, you MUST:**
1. Show the user what you intend to change (file path, summary of change)
2. Wait for explicit approval ("yes", "ok", "approved", "do it", etc.)
3. Only then make the change

**Never auto-commit, auto-fix, or auto-modify without user consent.**

**The evidence rule is NOT relaxed in dev mode.** Development access lets you
change the framework; it does not let you write a locator that no capture
supports. An invented id is a defect at every permission level.

### On Failure Behavior:

If a quality gate fails or a tool produces an error:

1. **STOP** - Pause workflow
2. **ANALYZE** - Identify root cause (framework bug, gate bug, AI behavior, device/env)
3. **DISCUSS** - Report to user with options:
   ```
   Issue detected at Step [X].

   Error: [error message]
   Root cause: [analysis]

   Options:
   1. Fix the framework/gate code and retry (requires approval)
   2. I will fix manually - continue workflow
   3. Log defect and abort
   ```
4. **WAIT FOR APPROVAL** - Do not proceed until user chooses an option
5. **FIX** - Only if user approves option 1, fix the framework code
6. **LOG DEFECT** - Add entry to `docs/DEFECT_LOG.md` using standard format
7. **RESTART** - After fix, restart from Step 1 to verify clean run

### Defect Logging Format:

```markdown
### [DEF-XXX] Brief Description
**Severity:** CRITICAL | HIGH | MEDIUM | LOW
**Status:** OPEN
**Run ID:** YYYY-MM-DD-RX
**Caught By:** Step X (workflow name)
**Layer:** Interface | Screen | Task | Role | Quality Gate | AI Orchestration | Skill
**Platform:** ios | android | ios-web | android-web
**File:** `path/to/file.py`

**Error Message:**
[exact error]

**Description:**
[what went wrong]

**Fix Required:**
[proposed fix]
```

---

Do NOT proceed to Step 2 until user provides their requirement.
