# Isagawa Kernel — Agent Guide

You are an AI agent operating within the Isagawa QA Platform. This file defines how you select the correct framework repo, initialize it, and operate within it. Read this before taking any action in an isagawa-qa workspace.

---

## Step 1: Identify the Correct Framework Repo

Use this decision table to determine which repo applies to the current task:

| If the project needs... | Use this repo |
|------------------------|---------------|
| Native iOS or Android app testing on a simulator, emulator or device (Python + Appium) | `isagawa-qa/platform-mobile-apps` |
| Web UI testing in a desktop browser (Python) | `isagawa-qa/platform-selenium` |
| Web UI testing in a desktop browser (TypeScript) | `isagawa-qa/platform-playwright` |
| Docker container image validation | `isagawa-qa/platform-docker` |
| SSH-accessible Linux image validation | `isagawa-qa/platform-ssh` |
| LLM pipeline / AI output evaluation | `isagawa-qa/test-platform-deepeval` |

A website opened in a phone's browser is a mobile-web target of this repo (`ios-web`, `android-web`), but check what runs before promising it. iOS real devices (`L3-03`), iOS hybrid (`L3-04`) and iOS mobile web (`L3-05`) are **BLOCKED with their gates OPEN**; Android hybrid and mobile web (`L3-02`) have not been delivered. iOS today means a simulator. The full table is `PLATFORM_GUIDE.md` § What Runs Today. If unclear, ask the developer before proceeding. Do not guess.

---

## Step 2: Verify Checkout

Confirm the repo is checked out locally before taking any action. From the framework root:

```bash
test -f CLAUDE.md && test -f framework/interfaces/mobile_interface.py && echo "platform-mobile-apps is checked out"
```

If either file does not exist, the repo is not checked out (or this is the wrong directory). Stop and instruct the developer:

```text
The platform-mobile-apps repository must be checked out locally before tests can be generated or run.

Clone it:
  git clone https://github.com/isagawa-qa/platform-mobile-apps.git

Then set up the Python environment, the Appium tooling and a device per SETUP.md.
```

---

## Step 3: Initialize

Once checked out, read the framework's integration context:

```text
INTEGRATION.md
```

This file defines:
- How to point the session at the developer's app build
- How to run tests
- How to generate tests
- The device gap: which targets run today and which are blocked
- Failure protocol
- Framework constraints (what you may and may not modify)

Do not proceed past this step until you have read `INTEGRATION.md`.

A fresh clone ships **before domain setup**: no protocol and no domain hooks. The first session in it must run `/kernel/session-start`, then `/kernel/domain-setup`, in that order, and restart Claude Code when domain setup says so. Domain setup also probes the host tooling and asks which device location each platform uses.

---

## Step 4: Understand the Kernel

Every isagawa-qa framework repo contains the **Isagawa Kernel** — a hook-based enforcement system in `.claude/`. It governs your behavior automatically. The kernel is identical across the family; only the domain protocol that `/kernel/domain-setup` generates is specific to this repo.

### What the Kernel Does

| Trigger | Effect |
|---------|--------|
| Session start | Requires `/kernel/session-start` before any work |
| Every 30 actions (the `actions_limit` default) | Blocks writes until you invoke `/kernel/anchor` |
| Test failure | Sets `needs_learn: true`, blocks writes until `/kernel/learn` |
| Anchor violation | Requires `/kernel/learn` before continuing |

### When You See `BLOCKED:`

The kernel has stopped you. The message always includes the exact command to run. Run it immediately. Do not work around it — not with a different tool, and not by editing state files.

```text
BLOCKED: 30 actions since last anchor

FIX:
1. Invoke /kernel/anchor
→ /kernel/anchor
```

### Kernel Commands

| Command | When to invoke |
|---------|---------------|
| `/kernel/session-start` | First action of every session |
| `/kernel/domain-setup` | Once, in a fresh clone, right after session-start |
| `/kernel/anchor` | Every 30 actions (hook-enforced) or when context drifts |
| `/kernel/learn` | After any test failure fix |
| `/kernel/fix` | Before applying any fix — impact assessment |
| `/kernel/complete` | When a task is fully done |

---

## Step 5: Operate Within Framework Constraints

Each repo defines what you may and may not modify. Always read `INTEGRATION.md` for the current repo's constraint list. For this repo:

**You may generate or modify:**
- Test files (`tests/`), including test data (`tests/<workflow>/data/`)
- Screen Object files (`framework/screens/`)
- Task layer files (`framework/tasks/`)
- Role layer files (`framework/roles/`)

**You must not modify:**
- The interface layer (`framework/interfaces/`)
- Core utilities and config (`framework/resources/`)
- The reference implementation (`framework/_reference/`)
- Kernel files (`.claude/`)
- `CLAUDE.md`

What each layer owns is the 5-layer contract in [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#the-5-layer-contract). Two mobile rules on top of it are enforced by `/pr`: every locator value must appear in a captured page source, and a Screen constant carries a key only for a platform that was captured.

---

## Step 6: Document Coverage in the Developer's Project

After generating or running tests, create or update `QA_COVERAGE.md` in the developer's application repo:

```markdown
# QA Coverage

Tests for this project live in the Isagawa platform-mobile-apps framework.
platform-mobile-apps must be checked out locally to run tests.

## Coverage Map

| Feature | User Story | Platforms | Test Location |
|---------|-----------|-----------|----------------|
| [Feature] | As a [persona], I want to [action] | ios, android | tests/[workflow]/test_[feature].py |

## Running Tests

See platform-mobile-apps/DEVELOPER_GUIDE.md for setup and execution instructions.
```

This is the only test-related file that belongs in the developer's project.

---

## Failure Protocol

On any test failure, follow HITL — do not auto-fix:

1. **STOP** — halt immediately
2. **REPORT** — test name, error, file location, and the screenshot and page source saved under `artifacts/`
3. **ANALYZE** — expected vs actual, likely cause (locator, timing, device or environment)
4. **DISCUSS** — ask: log defect in `docs/DEFECT_LOG.md`?
5. **PRESENT OPTIONS** — 2-3 fix approaches with tradeoffs
6. **WAIT FOR APPROVAL** — do not fix until approved
7. **FIX + RE-TEST** — implement approved fix, re-run same tests
8. **LEARN** — invoke `/kernel/learn` to record the lesson

---

## CI/CD Awareness

If the developer asks about running tests in a pipeline, flag this:

> The framework repo must be available in the CI environment, and iOS needs a macOS runner. Options:
> - **Git submodule** (recommended) — pins the tested version
> - **Pipeline checkout step** — clones the framework repo before tests run
> - **Shared runner** — machine with all repos permanently available

The free GitHub `macos-15` runner boots an iOS **simulator**; it never provides a real device. You cannot configure a pipeline automatically. Raise it with the developer.

---

## Reference

| Resource | Location |
|----------|----------|
| Platform guide (which repo, what runs today) | `PLATFORM_GUIDE.md` |
| Repo setup instructions | `SETUP.md` |
| Human developer guide and the 5-layer contract | `DEVELOPER_GUIDE.md` |
| Cross-workspace context | `INTEGRATION.md` |
| Device and app config | `framework/resources/config/environment_config.json` |
| Kernel state | `.claude/state/` (created by `/kernel/session-start`) |
| Lessons log | `.claude/lessons/lessons.md` (not shipped; created on first use) |
