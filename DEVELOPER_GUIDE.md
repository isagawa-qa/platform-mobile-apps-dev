# Developer Guide — Isagawa QA Platform (Mobile)

This is a centralized Appium test framework for native iOS and Android apps. You develop your app in your own workspace; this framework tests it from here.

---

## How It Works

Your app is installed on a simulator, an emulator or a device. This framework opens an Appium session against it, taps through it, and asserts behavior — just like a user would. There is no URL to point at: the session's capabilities launch the app. Tests are organized by workflow, not by framework feature.

```text
Your App Workspace          platform-mobile-apps
──────────────────          ────────────────────
You build features   →      Claude runs tests against your app build
Your CLAUDE.md       →      imports INTEGRATION.md from here
                            registers your app under "apps" in environment_config.json
                            runs: pytest -m ios --platform=ios
```

---

## Step 1: Register Your App and Pick a Device Location

Apps live under `apps` in `framework/resources/config/environment_config.json`. This is the entry the platform ships for its public reference app, verbatim:

```json
{
  "demo_native": {
    "android": {
      "path": "${ANDROID_APP_PATH:-apps/mda-2.2.0-25.apk}",
      "app_id": "${ANDROID_APP_ID:-com.saucelabs.mydemoapp.android}"
    },
    "ios": {
      "path": "${IOS_APP_PATH:-apps/SauceLabs-Demo-App.app}",
      "app_id": "${IOS_BUNDLE_ID}"
    },
    "cloud": {
      "android": "${CLOUD_ANDROID_APP}",
      "ios": "${CLOUD_IOS_APP}"
    }
  }
}
```

Add your app as a sibling key with the same shape, and set the platform's `default_app` to it.

| Key | Required | Description |
|-----|----------|-------------|
| `<family>.path` | for `local`/`ci` | The `.apk` or simulator `.app` the session installs. Lives in git-ignored `apps/`, never committed |
| `<family>.app_id` | for `remote` iOS | Package or bundle id, used when the app is already installed |
| `cloud.<family>` | for `cloud` | The provider's app reference (for example `bs://…`) |

Every `${VAR}` resolves from `.env` (copy `.env.example`). Each platform also has a **device location** — where the device actually is — chosen per platform in `.env`:

| `MOBILE_DEVICE_LOCATION_IOS` / `_ANDROID` | Meaning |
|---|---|
| `local` | A simulator or emulator on this machine, Appium at `127.0.0.1:4723` |
| `ci` | The GitHub `macos-15` runner boots an iOS simulator (iOS only) |
| `remote` | An Appium server somewhere else, reached by URL — including the free `ios-tunnel` workflow |
| `cloud` | A device cloud such as BrowserStack (needs credentials) |

A device location that cannot work on this host fails at setup with the reason and the alternatives. Local iOS needs macOS, because the Apple toolchain does not exist anywhere else.

---

## Step 2: Set Up Cross-Workspace Access

Add one line to your project's `CLAUDE.md`. Claude Code resolves an `@` import relative to the file, so with both repos checked out side by side:

```text
@../platform-mobile-apps/INTEGRATION.md
```

Then use this prompt to activate it:

```text
I'm working on [your app name]. The Isagawa platform-mobile-apps framework is
checked out next to this project. Please read ../platform-mobile-apps/INTEGRATION.md
so you understand how to generate and run tests for this app.
```

Claude will confirm it has read the file and is ready to generate tests or run existing ones against your app.

---

## Step 3: Generate Tests for Your App

The repo ships **before domain setup**: no protocol and no domain hooks yet. From inside the platform directory, run these in Claude Code, in this order (see [SETUP.md Step 6](SETUP.md#step-6-run-kernelsession-start-then-kerneldomain-setup)):

```text
/kernel/session-start
/kernel/domain-setup
/qa-workflow
```

Domain setup asks you to restart Claude Code once; `/qa-workflow` then asks for a user story:

```text
As a [persona], I want to [action]

Example:
As a shopper, I want to add a product to my cart
```

Step 4 of the workflow opens a live Appium session through the `appium-mcp` discovery server, captures the page source of every screen it touches, and only then writes code. It generates one folder per layer:

| Layer | Location | Purpose |
|-------|----------|---------|
| Screen Object | `framework/screens/{workflow}/` | Per-platform locators + atomic screen actions |
| Task | `framework/tasks/{workflow}/` | Domain operations (open catalog, add to cart) |
| Role | `framework/roles/{workflow}/` | Workflow orchestration |
| Test | `tests/{workflow}/` | AAA-pattern assertions |
| Test data | `tests/{workflow}/data/*.json` | Read through the `workflow_data` fixture |

---

## Step 4: Run Tests

From the platform root, with the simulator or emulator and the Appium server running:

```bash
# The shipped reference flow on iOS (exactly what CI runs)
PYTHONPATH=tests python -m pytest -p conftest framework/_reference/tests -m ios --platform=ios -v

# Every generated suite for one platform (tests marked for the other family are deselected)
python -m pytest -m ios --platform=ios -v
python -m pytest -m android --platform=android -v

# No device yet: confirm the project collects without opening a session
python -m pytest --collect-only

# With an HTML report
python -m pytest -m ios --platform=ios -v --html=tests/_reports/report.html --self-contained-html
```

To run one workflow, add its folder (for example `tests/catalog/`) after `pytest`. `--platform` takes any key under `platforms` in the config (`ios`, `android`, `ios-web`, `android-web`); with no flag it reads `PLATFORM` from the environment, then `default_platform`. The reference flow needs `-p conftest` because `framework/_reference/` is an exemplar outside `tests/`, so `tests/conftest.py` is not its ancestor. It is marked `ios`, so on Android it is deselected.

---

## The 5-Layer Contract

This is the contract every generated file follows. It is stated in full here and nowhere else; the other guides link to this section.

```text
Test → Role → Task → Screen → MobileInterface
```

| Layer | Owns | Never does |
|-------|------|-----------|
| **Test** | Arrange / Act / Assert; one Role call per phase; asserts through Screen state-checks | Locators, capabilities, building a driver |
| **Role** | A persona's workflow; composes Tasks; each workflow method calls several Tasks | Returns values, imports Screens, catches exceptions |
| **Task** | One domain operation; composes Screen Objects in fluent chains | Locators, returns values, `try/except` |
| **Screen** | Platform-keyed locator constants, `locator()`, atomic actions returning `self`, state-checks | Decorators, imports from tasks/roles, raw driver calls |
| **MobileInterface** | The Appium driver: finders, waits, taps, typing, gestures, contexts, app lifecycle | Domain vocabulary, screenshots (conftest owns failure evidence) |

| Layer | Decorator | On the constructor? |
|-------|-----------|---------------------|
| Screen | none | no |
| Task | `@autologger.automation_logger("Task")` | no |
| Role | `@autologger.automation_logger("Role")` | yes — `"Role Constructor"` |
| Test | `@autologger.automation_logger("Test")` | no |

Three mobile rules sit on top of the layering:

- **Locators are evidence.** Every id appears verbatim in a captured page source. A locator nobody captured is a guess, and `/pr` rejects it.
- **One key per observed platform.** Each constant maps `"ios"` / `"android"` to an `(AppiumBy, value)` pair. There is no `"default"` key and no fallback: `locator()` raises on a missing platform.
- **Platform choices are made once, at construction.** Where platforms differ in *sequence* (one tap to the catalog on iOS, two on Android), a per-platform Screen is picked when the Task is built. No Task, Role or Test branches on platform.

The layer-by-layer walkthrough with real excerpts is in [docs/architecture.md](docs/architecture.md).

---

## Available Commands (inside platform-mobile-apps)

| Command | What It Does |
|---------|-------------|
| `/qa-workflow` | 5-step guided test generation — a user story in, a captured and tested suite out |
| `/qa-workflow-dev` | Same, with full permissions (for framework changes, each one approved) |
| `/run-test [path]` | Run a test path with the HITL failure protocol and an HTML report |
| `/pr` | Review changed code against the layer contract and the evidence rule |
| `/qa-reuse-check` | Scan for duplicate Screen, Task and Role modules before building new ones |
| `/qa-pre-construction` | Checkpoint the workflow reads before writing any code |
| `/qa-propose-fix` | Checkpoint before any fix is applied |
| `/qa-on-failure` | Checkpoint on any test failure or error |

---

## Test Reports

`/run-test` writes `tests/_reports/report.html`. Its header records the platform, device location, device, automation name and Appium server for the run. On a failure, `tests/conftest.py` saves a screenshot and the page source under `artifacts/` before the session closes. Both folders are git-ignored.

---

## Framework Architecture

```text
platform-mobile-apps/
├── framework/
│   ├── interfaces/     ← MobileInterface (core, do not modify)
│   ├── _reference/     ← The canonical Screen/Task/Role/Test set the agent reads first
│   ├── screens/        ← Generated Screen Objects, one folder per workflow
│   ├── tasks/          ← Generated Tasks
│   ├── roles/          ← Generated Roles
│   └── resources/
│       └── config/
│           └── environment_config.json   ← Register your app and devices here
├── tests/
│   ├── {workflow}/     ← Generated tests and their data/
│   ├── conftest.py     ← Fixtures: config, device, driver, mobile, test_users, workflow_data
│   └── _reports/       ← HTML test reports
├── apps/               ← App builds fetched at setup (git-ignored)
└── INTEGRATION.md      ← Import this from your project's CLAUDE.md
```

`framework/screens`, `tasks` and `roles` appear when `/qa-workflow` first writes into them.

---

## Dependencies & Constraints

### platform-mobile-apps Must Be Checked Out

Your tests live here, not in your application repo. This means:

- Every developer who runs tests needs this repo checked out, plus the host tooling in [SETUP.md](SETUP.md)
- Your application repo holds no test files — only a `QA_COVERAGE.md` that maps features to test locations here
- Your app build is never committed here; it is fetched or built into the git-ignored `apps/`, or referenced by id

### CI/CD

If your pipeline needs to run these tests, this repo must be available there:

| Approach | How |
|----------|-----|
| Git submodule | Add this repo as a submodule in your app repo — pins the tested version |
| Pipeline checkout step | Check this repo out alongside your app before running tests |
| Shared runner | A machine with both repos permanently checked out |

For iOS, the shipped workflows already run on the free GitHub `macos-15` runner, which boots a **simulator**, not a real device. iOS real-device coverage is gate `L3-03`, **BLOCKED with the gate OPEN** until a device cloud or a Mac-built WebDriverAgent is provided; iOS hybrid (`L3-04`) and iOS mobile web (`L3-05`) are BLOCKED the same way. See [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md#what-runs-today).

---

## When Tests Fail

`/run-test` follows a Human-in-the-Loop (HITL) protocol on failure:

1. **STOP** — does not auto-fix
2. **REPORT** — shows test name, error, location, and the saved screenshot and page source
3. **ANALYZE** — expected vs actual; a locator, timing or environment cause
4. **DISCUSS** — asks whether to log a defect in `docs/DEFECT_LOG.md`
5. **FIX OPTIONS** — presents 2-3 approaches with tradeoffs
6. **APPROVE** — you choose the fix approach
7. **FIX + RE-TEST** — implements and re-runs, then `/kernel/learn` records the lesson

You stay in control of every fix decision.
