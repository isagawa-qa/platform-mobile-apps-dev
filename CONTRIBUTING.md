# Contributing to Isagawa QA Platform (Mobile)

Thank you for your interest in contributing. This repository generates Appium tests for native iOS and Android apps under a strict layered architecture, enforced at runtime by the [Isagawa Kernel](https://github.com/isagawa-co/isagawa-kernel). Contributions are welcome as long as they preserve that architecture.

## Architecture

This project uses a **5-layer architecture** of Test, Role, Task, Screen Object and MobileInterface. The full contract — what each layer owns, what it never does, and which decorator it carries — is stated once, in [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#the-5-layer-contract). Read it there rather than from a summary; a restated rule is how a contract quietly forks.

| Layer | Responsibility |
|-------|---------------|
| **Test** | Orchestrates Roles, asserts results via Screen state-check methods |
| **Role** | Coordinates Tasks into a persona's workflow |
| **Task** | Performs one domain operation, composes Screen Objects |
| **Screen Object** | Platform-keyed locators + atomic actions for one screen, fluent API (`return self`) |
| **MobileInterface** | Appium wrapper — waits, gestures, contexts, app lifecycle, logging, re-raise |

**Key rules for contributors:**
- Locators live *only* in Screen Objects, and every value must appear in a captured page source
- A Screen constant carries a key only for a platform that was captured; there is no `"default"` key
- Tasks and Roles never return values and never branch on platform
- `@autologger.automation_logger` on every Task, Role, and Test method

See [docs/architecture.md](docs/architecture.md) for the layer-by-layer walkthrough with excerpts. Before writing any code, read the reference implementations in [`framework/_reference/`](framework/_reference/) — the kernel reads them first and will not generate a layer without its reference.

---

## What We're Looking For

We welcome contributions that extend the platform's reach while preserving the layered architecture. Here are the areas where help is most needed:

### Framework Ports

The current implementation is Python + Appium (XCUITest and UiAutomator2). We'd welcome the same layered architecture on other mobile stacks:

- **Espresso** (Kotlin/Java) — an Android-native MobileInterface, keeping Task/Role/Test unchanged
- **XCUITest native** (Swift) — an iOS-native implementation for teams already in Xcode
- **Maestro** — a YAML-driven variant that keeps the Screen/Task separation

### Language Support

Bring the layered architecture to other language ecosystems on top of Appium:

- **TypeScript/JavaScript** — WebdriverIO + Appium with the same layer separation
- **Java** — Appium java-client with equivalent Screen Object and Task patterns
- **C#/.NET** — Appium .NET client with NUnit/xUnit

### New Test Layers

Extend the architecture beyond native screens — same layered approach, different interfaces:

- **Hybrid and mobile web** — the Flow 2 reference (a WebView screen, switch in and back out) is designed but not yet delivered; see `L3-02` in [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md#what-runs-today)
- **API layer** — an HTTP-client interface under the same Task/Role/Test layers, for setting up app state before a UI flow

### CI/CD & Infrastructure

- **Android CI** — there is no Android workflow today; iOS runs on the GitHub `macos-15` runner (a simulator)
- **Real-device iOS** — `L3-03`, `L3-04` and `L3-05` are **BLOCKED with their gates OPEN** until a device cloud or a Mac-built WebDriverAgent is available; wiring and proving either is welcome
- **Docker** — containerized Appium host for Android emulators

### Reporting & Observability

- **Allure** integration for richer test reports
- **HTML report** improvements beyond pytest-html (device, platform and capture links per test)
- **Slack/Teams notifications** on test failure

### Example Test Suites

Complete working examples on public demo apps, built with `/qa-workflow` from live captures:

- Login and logout (the reference flow has no login step today)
- Checkout — the reference flow stops at the cart's "Proceed To Checkout"
- Search, sort and filter on a catalog
- Multi-role scenarios across two sessions

### Documentation

- Tutorials and walkthroughs, especially per host (macOS, Windows)
- Video guides
- Translations

---

## Development Setup

### 1. Clone and install

```bash
git clone https://github.com/isagawa-qa/platform-mobile-apps.git
cd platform-mobile-apps
python -m venv .venv
```

Activate the environment the way your host does it ([SETUP.md Step 2](SETUP.md#step-2-python-environment)), then:

```bash
python -m pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure MCP (required for AI-powered test generation)

The platform uses [appium-mcp](https://github.com/appium/appium-mcp) to discover elements on a live device. It is pre-configured in `.mcp.json`:

```json
{
  "mcpServers": {
    "appium-mcp": {
      "type": "stdio",
      "command": "npx",
      "args": ["appium-mcp@1.94.1"],
      "env": {
        "AI_VISION_ENABLED": "false",
        "APPIUM_MCP_ON_CLIENT_DISCONNECT": "delete_all"
      }
    }
  }
}
```

**Prerequisites:** Node.js 22+ (`node --version` to check) and npm.

**Verify MCP is working:**
```bash
npx appium-mcp@1.94.1 --version
```

Host-specific notes — the Android SDK path, and driving a device on another host — are in [SETUP.md § The discovery server](SETUP.md#the-discovery-server).

### 3. Configure environment

Edit `.env` to choose where each platform's device is. Comments go on their own line; a value with no default must be set.

```text
MOBILE_DEVICE_LOCATION_IOS=local
MOBILE_DEVICE_LOCATION_ANDROID=local
```

`local` iOS needs a macOS host; on Windows set iOS to `remote` and follow [SETUP 4b.1](SETUP.md#4b1-ios-on-windows). Every other variable (app paths, device ids, Appium URLs, cloud credentials) is listed with its default in `.env.example`. Then complete your host section: [macOS](SETUP.md#macos-host) or [Windows](SETUP.md#windows-host).

### 4. Run tests

With no device yet, confirm the project collects:

```bash
python -m pytest --collect-only
```

With a device and Appium running, the reference flow and your platform's suites:

```bash
PYTHONPATH=tests python -m pytest -p conftest framework/_reference/tests -m ios --platform=ios -v
python -m pytest -m android --platform=android -v
```

---

## PR Process

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow the layered architecture — read `framework/_reference/` before writing code, and run `/pr` on your change
4. Ensure tests pass for the platform you changed, and that `python -m pytest --collect-only` still collects
5. Submit a PR with a clear description of what layer(s) your change touches, and which capture backs any new locator

For framework ports, new language support or a new device provider, open an issue first to discuss the approach.

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `refactor:` — Code restructuring
- `test:` — Test additions/changes
- `docs:` — Documentation
- `chore:` — Maintenance

## Questions?

Open an issue or reach out at **[alain@isagawa.co](mailto:alain@isagawa.co)**.

This project is under the Isagawa Proprietary License (evaluation use only); see [LICENSE](LICENSE). Contributions are accepted under the same terms.
