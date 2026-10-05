# Isagawa QA Platform (Mobile)

![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Appium](https://img.shields.io/badge/Appium-3.7.0-green)

[![iOS Simulator PoC](https://github.com/isagawa-qa/platform-mobile-apps-dev/actions/workflows/ios-poc.yml/badge.svg)](https://github.com/isagawa-qa/platform-mobile-apps-dev/actions/workflows/ios-poc.yml)
[![iOS reference suite](https://github.com/isagawa-qa/platform-mobile-apps-dev/actions/workflows/ios-reference.yml/badge.svg)](https://github.com/isagawa-qa/platform-mobile-apps-dev/actions/workflows/ios-reference.yml)
[![iOS interactive tunnel](https://github.com/isagawa-qa/platform-mobile-apps-dev/actions/workflows/ios-tunnel.yml/badge.svg)](https://github.com/isagawa-qa/platform-mobile-apps-dev/actions/workflows/ios-tunnel.yml)
[![prod-test L3](https://github.com/isagawa-qa/platform-mobile-apps-dev/actions/workflows/prod-test-l3.yml/badge.svg)](https://github.com/isagawa-qa/platform-mobile-apps-dev/actions/workflows/prod-test-l3.yml)

AI-powered Appium test automation for native and hybrid mobile apps, with a 5-layer architecture and runtime enforcement. Describe a requirement in plain English and the AI agent opens a live device session, discovers elements per platform, and generates Screen objects, Tasks, Roles, and Tests that follow strict separation of concerns. Every action is gated by the [Isagawa Kernel](https://github.com/isagawa-co/isagawa-kernel), so the agent can only produce code that matches the architecture.

---

## Status

This is the **development** repository. It is promoted to `isagawa-qa/platform-mobile-apps` once a platform path is green here.

Proven today, on record in [Actions](https://github.com/isagawa-qa/platform-mobile-apps-dev/actions):

- **iOS on CI** runs green on the GitHub `macos-15` runner: the reference suite (`ios-reference.yml`), the simulator PoC (`ios-poc.yml`), and the live L3 batch (`prod-test-l3.yml`) all execute against a real iOS simulator.
- **Android on a Windows host** is recorded end to end in [`SETUP.md`](SETUP.md#windows-host) (JDK 17, Android SDK build-tools, an API 34 AVD, Appium with the UiAutomator2 driver, `/qa-workflow` discovery and generated tests). There is no Android CI workflow.

Everything else in the support matrix below is an install path without a run record, or needs an input this repo does not ship (a device id, an Appium endpoint, or cloud credentials).

---

## The Problem

AI can generate mobile tests in seconds. Mobile makes the failure modes worse than web:

- Locators differ per platform, so one generated Screen object silently breaks on the other OS.
- A device, host OS, and Appium matrix means "works on my machine" rarely transfers.
- Appium sessions are flaky; without discipline the agent papers over failures with retries and sleeps.
- The same architecture mistakes repeat every session.

Generate, breaks on Android, fix, breaks the iOS locators, start over.

---

## The Solution

This platform pairs a **5-layer test architecture** with the **Isagawa Kernel**, a self-building enforcement system that runs inside the AI agent.

The kernel does not watch the agent from outside. It manages the agent from within: it reads the reference implementations before writing anything, chooses the per-platform Screen object at construction, and records a permanent lesson after every failure. Locators stay in Screen objects, business logic stays in Tasks and Roles, and the device matrix is declared once in config.

---

## How It Works

When you invoke `/qa-workflow`, the agent runs a 5-step pipeline with self-enforcing gates. There is no URL: a native app is launched from the session capabilities; a `-web` platform targets the device browser.

```
/qa-workflow
    |
Step 1: USER INPUT
    persona, app (an entry under `apps` in environment_config.json), platform, workflow id
    Gate: persona + app + platform present; platform in {ios, android, ios-web, android-web}
    |
Step 2: PRE-FLIGHT
    resolve platform -> device_location, pick a credential strategy
    Gate: the selected device_location resolves and the device or simulator is reachable
    |
Step 3: AI PROCESSING
    BDD scenarios, expected states, the screens the workflow touches
    Gate: expected states defined for each step
    |
Step 4: CAPTURE + CONSTRUCTION
    open a live Appium session, capture page source per screen, read the reference files,
    generate Screen, Task, Role, Test (/qa-pre-construction checkpoint runs first)
    Gate: 5-layer separation; locators live only in Screen objects
    |
Step 5: EXECUTION
    run pytest, capture the result
    Gate: test passes, or the failure is triaged with you (/qa-on-failure)
    |
COMPLETE -> lessons stored via /kernel/learn
```

---

## Architecture

### 5-Layer Separation of Concerns

| Layer | Responsibility | Example |
|-------|---------------|---------|
| **MobileInterface** | Appium driver wrapper: finders, waits, interactions, gestures, context switching, app lifecycle (50 public methods). | `mobile.tap()`, `mobile.switch_to_webview()` |
| **Screen (per platform)** | Locators as constants, chosen per platform at construction. Atomic actions, fluent, state-checks. | `ProductCatalogScreen.open_product()` |
| **Task** | One domain operation. Composes Screen objects. Decorated with `@automation_logger`. | `ShoppingTasks.add_product_to_cart()` |
| **Role** | User persona workflow. Composes Tasks. | `Shopper.browse_and_add_to_cart()` |
| **Test** | AAA pattern. Pytest fixtures. Assert via Screen state-checks. | `test_e2e_browse_and_add_to_cart()` |

```
Test (Arrange / Act / Assert)
  +-- Role (multi-task workflow, user persona)
       +-- Task (single domain operation)
            +-- Screen (one screen, per-platform locators, atomic actions)
                 +-- MobileInterface (Appium wrapper, waits, gestures, contexts)
```

The per-platform Screen is chosen once at construction (one tap to the catalog on iOS, two on Android), so Tasks and Roles stay platform-agnostic.

### Reference Implementations

The framework ships canonical code in `framework/_reference/`. The agent reads these before generating anything.

| File | Layer | Purpose |
|------|-------|---------|
| `interfaces/mobile_interface.py` | Interface | `MobileInterface`: Appium wrapper (finders, waits, gestures, contexts, app lifecycle) |
| `_reference/README.md` | Index | Which reference file to read per layer |
| `_reference/navigation/ios_navigation_screen.py` | Screen | iOS bottom tab bar between catalog, cart, menu |
| `_reference/navigation/android_navigation_screen.py` | Screen | Android header and drawer navigation |
| `_reference/screens/product_catalog_screen.py` | Screen | Wait for catalog, read a product, open a product |
| `_reference/screens/product_detail_screen.py` | Screen | Read product, adjust quantity, add to cart |
| `_reference/screens/cart_screen.py` | Screen | Verify what was added, move to checkout |
| `_reference/tasks/shopping_tasks.py` | Task | Browse the catalog and add a product to the cart |
| `_reference/roles/shopper.py` | Role | Shopper persona orchestrating Tasks |
| `_reference/tests/test_e2e_browse_and_add_to_cart.py` | Test | End-to-end browse, open, add to cart, verify |
| `resources/config/environment_config.json` | Config | Single source of truth for tooling pins, apps, and device locations |
| `resources/utilities/autologger.py` | Utility | `automation_logger` decorator: logs entry, exit, and timing |

---

## Kernel Enforcement

The [Isagawa Kernel](https://github.com/isagawa-co/isagawa-kernel) gates every action at runtime. It is not a linter or a post-hoc checker.

- **Session gating.** The agent cannot write code until `/kernel/session-start` initializes the session and loads protocol state.
- **Anchor cycling.** Every 30 actions the hook forces the agent to re-read its protocol via `/kernel/anchor`, preventing drift from the architecture.
- **Failure capture.** When a test fails the hook sets `needs_learn: true` and blocks further writes until `/kernel/learn` records the lesson permanently.
- **Reference-first construction.** Before generating any file the agent reads the matching reference implementation in `framework/_reference/`. No reference, no generation.
- **Human-in-the-loop triage.** On any failure the agent stops and triages with you (`/qa-on-failure`); production mode cannot modify framework internals.

---

## Support Matrix

What runs where today. `runs today` means an exercised path (a CI run on record, or an end-to-end run recorded in `SETUP.md`). For the `ci` row the executing host is the GitHub `macos-15` runner; each host column records whether a developer on that host can trigger it and see the result.

| Platform | Device location | macOS host | Windows host |
|---|---|---|---|
| iOS | local | supported, unverified | not supported |
| iOS | remote | needs IOS_DEVICE_APPIUM_URL + IOS_UDID | needs IOS_DEVICE_APPIUM_URL + IOS_UDID |
| iOS | cloud | needs BrowserStack credentials | needs BrowserStack credentials |
| iOS | ci | runs today | runs today |
| Android | local | supported, unverified | runs today |
| Android | remote | needs ANDROID_UDID + Appium endpoint | needs ANDROID_UDID + Appium endpoint |
| Android | cloud | needs BrowserStack credentials | needs BrowserStack credentials |
| Android | ci | not supported | not supported |

iOS has no local Apple toolchain on Windows, so local iOS is macOS only. Android has no `ci` device location by design. Per-cell evidence is kept with the engineering notes, not here.

---

## Quick Start

Full, host-specific steps live in [`SETUP.md`](SETUP.md). This section is the map.

### Prerequisites

- Python 3.10+ (3.12 in CI), Node.js 22+, JDK 17
- Appium 3.7.0 with the XCUITest (iOS) and UiAutomator2 (Android) drivers
- A simulator, emulator, or device for your platform
- [Claude Code](https://claude.ai/claude-code)

Host details: [`SETUP.md#prerequisites-all-hosts`](SETUP.md#prerequisites-all-hosts).

### Install

```bash
git clone https://github.com/isagawa-qa/platform-mobile-apps-dev.git
cd platform-mobile-apps-dev
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

See [`SETUP.md#step-2-python-environment`](SETUP.md#step-2-python-environment).

### Configure

App builds are downloaded at run time and never committed. Fetch the reference apps, then edit `framework/resources/config/environment_config.json` for your app and device. See [`SETUP.md#step-3-fetch-the-reference-apps`](SETUP.md#step-3-fetch-the-reference-apps).

Then complete your host section: [`SETUP.md#macos-host`](SETUP.md#macos-host) or [`SETUP.md#windows-host`](SETUP.md#windows-host), and verify with [`SETUP.md#step-5-verify-setup`](SETUP.md#step-5-verify-setup).

### Run

Boot your simulator or emulator and the Appium server (per your host section), then from Claude Code. The repo ships before domain setup (no protocol, no domain hooks yet), so the first two commands are both required, in this order:

```bash
claude                  # start in the project directory
> /kernel/session-start # initialize the session
> /kernel/domain-setup  # generate the protocol and domain hooks; restart Claude Code when it says so
> /qa-workflow          # generate your first test
> /pr                   # review generated code against the architecture
```

Details and the verify step: [`SETUP.md#step-6-run-kernelsession-start-then-kerneldomain-setup`](SETUP.md#step-6-run-kernelsession-start-then-kerneldomain-setup).

### Tests

```bash
pytest -m ios --platform=ios           # iOS reference suite (reachable simulator; what CI runs)
pytest -m android --platform=android   # Android reference suite (booted emulator/device + Appium)

pytest --collect-only                  # no device yet: confirm the project collects (no session)
```

The reference suite is documented at [`SETUP.md#step-7-run-the-reference-suite`](SETUP.md#step-7-run-the-reference-suite).

---

## Commands

| Command | Purpose |
|---------|---------|
| `/qa-workflow` | 5-step QA test generation, production mode (restricted permissions) |
| `/qa-workflow-dev` | 5-step QA test generation, development mode (full access with approval) |
| `/qa-pre-construction` | Pre-construction checkpoint, read before writing code in Step 4 |
| `/qa-on-failure` | On-failure checkpoint, invoke when any test fails |
| `/qa-propose-fix` | Propose-fix checkpoint, invoke before applying a fix |
| `/qa-reuse-check` | Scan for duplicate modules and present consolidation options |
| `/pr` | Instant PR review against the framework patterns |
| `/run-test` | Run tests with the testing skill protocol |

---

## Project Structure

```
platform-mobile-apps-dev/
+-- .claude/
|   +-- commands/                    # Kernel + QA workflow commands
|   |   +-- qa-workflow.md           # /qa-workflow (5-step, production)
|   |   +-- qa-workflow-dev.md       # /qa-workflow-dev (dev mode)
|   |   +-- pr.md                    # /pr (code review)
|   |   +-- kernel/                  # session-start, anchor, complete, learn, ...
|   +-- skills/
|   |   +-- qa-management-layer/     # 5-step QA workflow skill
|   |   +-- kernel-domain-setup/     # self-building kernel setup
|   |   +-- autonomous-cycling/      # numbered-task loop
+-- framework/
|   +-- _reference/                  # canonical patterns (read-before-write)
|   |   +-- navigation/              # per-platform navigation Screens
|   |   +-- screens/ tasks/ roles/ tests/
|   +-- interfaces/
|   |   +-- mobile_interface.py      # MobileInterface (Appium wrapper)
|   +-- resources/
|       +-- config/                  # environment_config.json
|       +-- utilities/               # automation_logger
+-- tests/
|   +-- conftest.py                  # pytest fixtures (config, device, driver, mobile)
|   +-- data/                        # test data
+-- .github/workflows/               # ios-poc, ios-reference, ios-tunnel, prod-test-l3
+-- apps/                            # app builds (downloaded at run time, gitignored)
+-- .mcp.json                        # Appium discovery MCP server
+-- CLAUDE.md                        # kernel instructions
+-- SETUP.md                         # host-specific setup guide
+-- requirements.txt
+-- LICENSE
```

---

## Troubleshooting

Start with [`SETUP.md#troubleshooting`](SETUP.md#troubleshooting). If a problem is a framework issue rather than your setup, report it on [GitHub Issues](https://github.com/isagawa-qa/platform-mobile-apps-dev/issues) for this repo.

---

## Other Platforms

| Platform | Domain | Repo |
|----------|--------|------|
| **platform-mobile-apps-dev** | Mobile (Appium) test automation | (this repo) |
| **platform-selenium** | Selenium web test automation | [isagawa-qa/platform-selenium](https://github.com/isagawa-qa/platform-selenium) |
| **platform-playwright** | Playwright web test automation | [isagawa-qa/platform-playwright](https://github.com/isagawa-qa/platform-playwright) |

---

## Contributing

Adding a screen, platform, or device provider? See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the architecture rules, the areas we're looking for, and the PR process.

---

## Contact

**Email:** [alain@isagawa.co](mailto:alain@isagawa.co)
**Web:** [isagawa.co](https://isagawa.co)

---

## License

Isagawa Proprietary License - Evaluation Use Only. See [LICENSE](LICENSE). Evaluation use only: no production use, modification, reverse engineering, or redistribution, and no reliance on output for compliance decisions without a commercial license. Software provided AS IS with no warranty. Commercial licensing via [alain@isagawa.co](mailto:alain@isagawa.co).
