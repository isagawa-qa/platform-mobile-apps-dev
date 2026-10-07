# Isagawa QA Platform (Mobile) — Integration Context

You are operating in a developer's application workspace. This file gives you the context to run automated Appium tests against that developer's iOS or Android app using the centralized Isagawa platform-mobile-apps framework.

The platform-mobile-apps directory is the directory containing this file. All test execution, file generation, and framework operations happen there — not in the developer's project.

---

## Your Role

When the developer asks you to test something, generate tests, or run QA:

1. Verify their app build is wired in (see below) and that a device is reachable for the platform they want
2. Run every command from the platform-mobile-apps root directory, using absolute paths
3. Execute the appropriate command
4. Report results back in context of the developer's feature

Do NOT write test files in the developer's project. All test artifacts belong in platform-mobile-apps. Never copy the developer's app binary into this repo: it is referenced by path or id, and the git-ignored `apps/` folder is the only place a build may sit.

---

## Registering a New App

There is no URL to register. A test session launches the app from its capabilities, so "registering" means telling the session which build to install or open, and on which kind of device.

The quickest route needs no config edit. The shipped `demo_native` entry reads its build from `.env`, so pointing these variables at the developer's build is enough:

| Variable | Meaning |
|----------|---------|
| `ANDROID_APP_PATH` / `ANDROID_APP_ID` | The `.apk` to install, or the package id of an installed app |
| `IOS_APP_PATH` / `IOS_BUNDLE_ID` | The simulator `.app` to install, or the bundle id of an installed app |
| `MOBILE_DEVICE_LOCATION_IOS` / `_ANDROID` | `local`, `ci`, `remote` or `cloud` — where the device is |

A separate, named entry under `apps` in `framework/resources/config/environment_config.json` is the alternative when one checkout tests several apps. That file is under `framework/resources/`, which production `/qa-workflow` may not modify, so ask the developer to add it, or use `/qa-workflow-dev` with their approval. Each platform names its app through `default_app`; this excerpt of the shipped config shows the fields:

```json
{
  "android": {
    "family": "android",
    "markers": ["android"],
    "default_app": "demo_native",
    "device_location": "${MOBILE_DEVICE_LOCATION_ANDROID:-local}"
  }
}
```

To see the registered apps and platforms, read that config file.

---

## Running Tests

```bash
# The shipped reference flow on iOS (what CI runs)
PYTHONPATH=tests python -m pytest -p conftest framework/_reference/tests -m ios --platform=ios -v

# Every generated suite for one platform
python -m pytest -m ios --platform=ios -v
python -m pytest -m android --platform=android -v

# No device yet: confirm the project collects
python -m pytest --collect-only

# With an HTML report
python -m pytest -m android --platform=android -v --html=tests/_reports/report.html --self-contained-html
```

To run one workflow, add its folder (`tests/<workflow>/`) after `pytest`. A device location that cannot work on this host fails at setup with the reason and the alternatives, so read that message before anything else.

---

## Generating Tests for a New Feature

When the developer asks to add tests for a feature, use the QA workflow (`/qa-workflow`). It reads these files from the platform-mobile-apps root:

```text
.claude/skills/qa-management-layer/SKILL.md
.claude/skills/qa-management-layer/steps/step-01.md
.claude/skills/qa-management-layer/steps/step-04.md
.claude/skills/qa-management-layer/steps/step-04-capture.md
.claude/skills/qa-management-layer/checkpoints/pre-construction.md
```

The workflow requires a user story in this format, plus the app and the platform:

```text
As a [persona], I want to [action]
```

Step 4 opens a live session through the `appium-mcp` discovery server (pinned in `.mcp.json`) and captures the page source of every screen before writing code, so a device must be running. Output goes to:
- `framework/screens/<workflow>/` — Screen Objects
- `framework/tasks/<workflow>/` — Tasks
- `framework/roles/<workflow>/` — Roles
- `tests/<workflow>/` — Test files, with test data in `tests/<workflow>/data/`
- `tests/_state/captures/` — the page sources every locator was read from

---

## Documenting Test Coverage in the Developer's Project

After generating or running tests, create or update a `QA_COVERAGE.md` file in the **developer's project** (not in platform-mobile-apps). This file is the dev project's record that tests exist externally.

```markdown
# QA Coverage

Tests for this app live in the Isagawa platform-mobile-apps framework.
platform-mobile-apps must be checked out and available locally to run tests.

## Coverage Map

| Feature | User Story | Platforms | Test Location in platform-mobile-apps |
|---------|-----------|-----------|----------------------------------------|
| Cart | As a shopper, I want to add a product to my cart | ios, android | tests/cart/test_add_to_cart.py |

## Running Tests

See platform-mobile-apps/DEVELOPER_GUIDE.md for setup and execution instructions.
```

Update this file each time new tests are added. It is the only test-related file that belongs in the developer's project.

---

## Dependencies & Constraints

### platform-mobile-apps Checkout Requirement

Tests live in platform-mobile-apps, not in the developer's project. Be aware:

- The developer must have platform-mobile-apps checked out locally, plus the host tooling in its `SETUP.md`, for any test operation to work
- If you cannot locate the platform-mobile-apps directory, stop and ask the developer to confirm its path before proceeding
- Never assume the path — if the developer's CLAUDE.md imports this file via `@<path>/INTEGRATION.md`, that path is your reference point for the root directory

### Device Gap

A test needs a running simulator, emulator or device and an Appium server for the platform. Local iOS requires a macOS host. From a Windows host, iOS runs on a simulator through the `ios-tunnel` workflow. iOS real devices (`L3-03`), iOS hybrid (`L3-04`) and iOS mobile web (`L3-05`) are **BLOCKED with their gates OPEN** — do not promise them. See `PLATFORM_GUIDE.md` § What Runs Today.

### CI/CD Gap

If the developer asks about running tests in a CI/CD pipeline, flag that platform-mobile-apps must be available in that environment, and that iOS needs a macOS runner. The options are:

- **Git submodule** — platform-mobile-apps added as a submodule in the app repo (recommended: pins the tested version)
- **Pipeline checkout step** — CI config checks out platform-mobile-apps alongside the app before running tests
- **Shared runner** — a machine with both repos permanently available

This is not something you can configure automatically. Raise it with the developer and refer them to `DEVELOPER_GUIDE.md` for the full breakdown.

---

## On Test Failure

Do NOT auto-fix. Follow this protocol (`/qa-on-failure`):

1. **STOP** — halt immediately
2. **REPORT** — test name, error message, file location, and the screenshot and page source saved under `artifacts/`
3. **ANALYZE** — expected vs actual; a locator, timing or environment cause
4. **DISCUSS** — ask developer: log defect in `docs/DEFECT_LOG.md`?
5. **PRESENT OPTIONS** — 2-3 fix approaches with tradeoffs (`/qa-propose-fix`)
6. **WAIT FOR APPROVAL** — do not fix until approved
7. **FIX + RE-TEST**

---

## Framework Constraints

**You may generate or modify:**
- `tests/` — test files and test data
- `framework/screens/` — Screen Object files
- `framework/tasks/` — task files
- `framework/roles/` — role files

**Do not modify:**
- `framework/interfaces/` — MobileInterface
- `framework/resources/` — core utilities and config
- `framework/_reference/` — the reference implementation
- `.claude/` — skills, commands, hooks
- `CLAUDE.md`

---

## Code Pattern Rules

Before generating any framework code, read:
```text
framework/_reference/README.md
```

The 5-layer contract — what each layer owns, what it never does, and which decorator it carries — is stated once, in [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#the-5-layer-contract). Follow it exactly; do not work from a summary. Two mobile rules matter most when generating: every locator value must appear in a captured page source, and a Screen constant carries a key only for a platform that was captured.

---

## Reference Paths (relative to platform-mobile-apps root)

| Resource | Path |
|----------|------|
| Environment config | `framework/resources/config/environment_config.json` |
| Environment variables | `.env` (copy of `.env.example`, git-ignored) |
| Reference patterns | `framework/_reference/README.md` |
| Test reports | `tests/_reports/report.html` (written by `/run-test`) |
| Failure evidence | `artifacts/screenshots/`, `artifacts/page_source/` (written on failure) |
| Defect log | `docs/DEFECT_LOG.md` (created when the first defect is logged) |
| QA skill | `.claude/skills/qa-management-layer/` |
