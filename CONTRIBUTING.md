# Contributing to the Isagawa QA Platform (Mobile)

Thank you for your interest in contributing. This repository generates Appium
tests for native and hybrid mobile apps under a strict 5-layer architecture,
enforced at runtime by the [Isagawa Kernel](https://github.com/isagawa-co/isagawa-kernel).
Contributions are welcome as long as they preserve that architecture.

## Architecture

The platform uses a **5-layer architecture**: Test > Role > Task > Screen > MobileInterface.

| Layer | Responsibility |
|-------|---------------|
| **Test** | Arrange/Act/Assert; orchestrates Roles, asserts via Screen state-checks |
| **Role** | Composes Tasks into a user-persona workflow |
| **Task** | One domain operation; composes Screen objects |
| **Screen** | Per-platform locators as constants + atomic, fluent actions for one screen |
| **MobileInterface** | Appium driver wrapper: finders, waits, interactions, gestures, context switching, app lifecycle |

**Key rules:**
- Locators live *only* in Screen objects, as per-platform constants chosen once at construction.
- Business logic lives in Tasks and Roles; they stay platform-agnostic.
- The `@automation_logger` decorator goes on every Task, Role, and Test method.
- The per-platform Screen is selected at construction, so Tasks and Roles never branch on platform.

See the [Architecture section of the README](README.md#architecture) for the full
explanation. **Before writing any code, read the reference implementations in
[`framework/_reference/`](framework/_reference/)** — the kernel reads them first and
will not generate a layer without its reference.

## What We're Looking For

Contributions that extend the platform's reach while preserving the architecture:

### Coverage
- **New Screens, Tasks, and Roles** that model additional app flows, following the reference patterns.
- **Additional platforms** across the four supported keys — `ios`, `android`, `ios-web`, `android-web`.
- **Cloud device providers** (e.g. BrowserStack) wired through the existing `device_location` config and environment variables.

### Infrastructure & Observability
- An **Android CI** workflow (there is none today; iOS runs on the `macos-15` runner).
- **Reporting** improvements beyond `pytest-html`, and failure notifications.
- **Docker** or other containerized execution for the Appium host.

### Documentation
- Tutorials, walkthroughs, and setup notes for hosts and devices not yet covered in [`SETUP.md`](SETUP.md).

## Development Setup

Setup is host-specific (macOS and Windows differ for iOS vs Android). The full,
verified steps live in [`SETUP.md`](SETUP.md):

- Prerequisites for all hosts: [`SETUP.md#prerequisites-all-hosts`](SETUP.md#prerequisites-all-hosts)
- Your host section: [`SETUP.md#macos-host`](SETUP.md#macos-host) or [`SETUP.md#windows-host`](SETUP.md#windows-host)
- The Appium element-discovery MCP server (pre-wired in `.mcp.json`): [`SETUP.md#the-discovery-server`](SETUP.md#the-discovery-server)
- Verify your setup: [`SETUP.md#step-5-verify-setup`](SETUP.md#step-5-verify-setup)

App builds under test are downloaded at run time and never committed.

## PR Process

1. Fork the repo.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Follow the 5-layer architecture — read [`framework/_reference/`](framework/_reference/) before writing code.
4. Ensure tests pass for your platform: `pytest -m ios --platform=ios` (or the equivalent for your target). With no device yet, confirm the project still collects: `pytest --collect-only`.
5. Submit a PR describing which layer(s) your change touches.

For a new platform, provider, or large feature, open an issue first to discuss the approach:
[GitHub Issues](https://github.com/isagawa-qa/platform-mobile-apps-dev/issues).

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `refactor:` — Code restructuring
- `test:` — Test additions/changes
- `docs:` — Documentation
- `chore:` — Maintenance

## Questions?

Open an [issue](https://github.com/isagawa-qa/platform-mobile-apps-dev/issues) or
reach out at **[alain@isagawa.co](mailto:alain@isagawa.co)**.

This project is under the Isagawa Proprietary License (evaluation use only); see
[LICENSE](LICENSE). Contributions are accepted under the same terms.
