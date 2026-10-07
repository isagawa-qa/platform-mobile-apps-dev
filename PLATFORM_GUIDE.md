# Isagawa QA Platform — Platform Guide (Mobile)

The Isagawa QA Platform is a family of AI-powered test automation frameworks. Each framework targets a different testing domain. This repository is the mobile one: native iOS and Android apps, driven through Appium. This guide helps you decide whether it is the right one for your project and get started.

---

## Which Framework Do You Need?

| What are you testing? | Framework | Repo |
|----------------------|-----------|------|
| Native iOS and Android apps (Python + Appium) | **Mobile — this repo** | [platform-mobile-apps](https://github.com/isagawa-qa/platform-mobile-apps) |
| Web UI in a desktop browser (Python) | Desktop web | [platform-selenium](https://github.com/isagawa-qa/platform-selenium) |
| Web UI in a desktop browser (TypeScript) | Desktop web | [platform-playwright](https://github.com/isagawa-qa/platform-playwright) |
| Docker container images | Docker validation | [platform-docker](https://github.com/isagawa-qa/platform-docker) |
| SSH-accessible Linux images | SSH validation | [platform-ssh](https://github.com/isagawa-qa/platform-ssh) |
| LLM pipelines / AI output quality | DeepEval | [test-platform-deepeval](https://github.com/isagawa-qa/test-platform-deepeval) |

If your product is an app installed on a phone, start here. If it is a website opened in a desktop browser, this is not the repo — use the desktop web frameworks above. The two can run side by side; they do not share state.

---

## How Each Framework Works

All frameworks follow the same core pattern, and here it is low-code by design:

1. **You describe** what to test in plain English — a user story such as "As a shopper, I want to add a product to my cart"
2. **AI discovers** the app's screens on a live device and **generates** a complete, structured suite following the framework's architecture
3. **Tests run** against your app on a simulator, an emulator or a device
4. **Results report** with full HTML output, a screenshot and the page source of any failure

You write no locators and no Appium calls. Every element id the generated code uses is read from a page source captured live during step 2, never typed from memory.

Tests are centralized in the framework repo. Your application repo stays clean — it only holds a `QA_COVERAGE.md` that maps features to test locations here.

---

## Common Prerequisites

| Tool | Purpose |
|------|---------|
| Git | Clone repos |
| VS Code + Claude Code extension | AI-assisted test generation |
| GitHub account | Fork repos to contribute |

Mobile also needs Python 3.10+, Node.js 22+, JDK 17 (for Android), Appium with its drivers, and a simulator, emulator or device. The exact pins live once, in the `tooling` block of `framework/resources/config/environment_config.json`; [SETUP.md](SETUP.md) walks through them per host.

---

## Getting Started

### 1. Pick your framework from the table above

### 2. Clone and set up

Follow [SETUP.md](SETUP.md): prerequisites, the Python environment, fetching the public reference app into `apps/`, then the section for your host (macOS or Windows).

### 3. Connect your application

There is no URL to register. Add your app build under `apps` in `framework/resources/config/environment_config.json`, and pick a device location per platform in `.env` (`local`, `ci`, `remote` or `cloud`). [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#step-1-register-your-app-and-pick-a-device-location) shows the exact entry. Your app binary is never committed to this repo.

### 4. Work from your own project

This framework ships an `INTEGRATION.md` — a file you import into your project's `CLAUDE.md` that lets Claude run tests and generate coverage without leaving your workspace. With both repos checked out side by side, add one line:

```text
@../platform-mobile-apps/INTEGRATION.md
```

Then use this prompt to activate it:

```text
I'm working on [your app]. The Isagawa platform-mobile-apps framework is checked
out next to this project. Please read ../platform-mobile-apps/INTEGRATION.md so
you understand how to generate and run tests for this app.
```

Inside the framework, the first session runs `/kernel/session-start`, then `/kernel/domain-setup`, then `/qa-workflow`, in that order — see [SETUP.md Step 6](SETUP.md#step-6-run-kernelsession-start-then-kerneldomain-setup).

---

## What Runs Today

Stated per gate, so nothing is implied that has not run:

| Target | Status | Gate |
|--------|--------|------|
| iOS native on a **simulator**, GitHub `macos-15` runner (free on a public repo) | Runs — the `ios-reference` workflow executes the reference flow | — |
| iOS native on a **simulator**, driven from a Windows host | Runs — the `ios-tunnel` workflow exposes that runner's Appium server ([SETUP 4b.1](SETUP.md#4b1-ios-on-windows)) | — |
| Android native on a local emulator | Runs on a Windows host ([SETUP.md](SETUP.md#windows-host)); no Android CI workflow | `L3-01` LIVE-POSSIBLE |
| Android hybrid and Android mobile web | Not yet delivered — the hybrid flow has not run | `L3-02` LIVE-POSSIBLE |
| iOS native on a **real device** | **BLOCKED — gate OPEN.** Unblocked by a device-cloud plan (credentials in `.env`) or a WebDriverAgent built once on a Mac driving an iPhone on iOS 18+ | `L3-03` |
| iOS hybrid | **BLOCKED — gate OPEN.** Same unblock as `L3-03`, plus a Mac-built hybrid `.ipa` | `L3-04` |
| iOS mobile web (Safari) | **BLOCKED — gate OPEN.** Same unblock as `L3-03` | `L3-05` |

The free `macos-15` route is a simulator, never a real device. Gate statuses are recorded in [gate-contract.md](gate-contract.md).

---

## The Kernel

All frameworks are governed by the **Isagawa Kernel** — an enforcement layer built into each repo's Claude Code configuration. It:

- Tracks actions and forces periodic re-anchoring to protocol (every 30 actions by default)
- Blocks writes when a test failure hasn't been learned from
- Enforces Human-in-the-Loop (HITL) approval before any fix is applied
- Maintains a lessons log that persists across sessions

You will see `BLOCKED:` messages when the kernel enforces a gate. Follow the instruction shown — it always tells you the exact command to run. See [KERNEL_AGENT_GUIDE.md](KERNEL_AGENT_GUIDE.md) for the full agent-facing spec.

---

## Framework Architecture

All repos use a variant of the same layered pattern. In this repo the bottom layer is `MobileInterface`, the Appium wrapper, and the layer above it is the Screen Object — one per app screen, with locators keyed by platform. The full contract, layer by layer, is in [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#the-5-layer-contract), with worked excerpts in [docs/architecture.md](docs/architecture.md).

Each layer composes the layer below it. No layer skips. AI generates code into this structure — it never writes outside it.

---

## Dependencies & Constraints

### Framework repos must be checked out locally

Tests live in the framework repo, not in your application repo. Every developer who runs tests needs this repo checked out, plus the host tooling. Document this dependency in your application's `README.md`.

### CI/CD

If your pipeline needs to run these tests, this repo must be available in that environment:

| Option | How |
|--------|-----|
| Git submodule | Add this repo as a submodule — pins the tested version, clean CI checkout |
| Pipeline checkout step | Add a step that clones this repo before running tests |
| Shared runner | A machine with all repos permanently checked out |

Git submodule is recommended — it records exactly which framework version your app was tested against. For iOS, the runner must be macOS; the shipped `ios-reference.yml` workflow is a working example.

---

## Contributing

All repos accept PRs via fork. This forks the repo, clones your fork and sets `upstream`:

```bash
gh repo fork isagawa-qa/platform-mobile-apps --clone
```

Always create a clean branch from `main` before opening a PR. Never open a PR from a long-running feature branch — scope it to the change only. Details in [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Support

Open an issue in the relevant repo. Include:
- Which framework and version (tag)
- The exact error or `BLOCKED:` message
- The test path, the `--platform` key and the device location used
