# Setup Guide — platform-mobile-apps

Isagawa QA platform for mobile apps. Appium in the Interface, the same 5-layer
contract as platform-selenium: Test → Role → Task → Screen → Interface.

This repo ships **pre-domain-setup**. It carries the kernel but no generated
protocol, hooks, lessons or state — you generate those yourself at Step 5, and
nothing under `.claude/` works until you do.

## Prerequisites (all hosts)

> **The versions below are a convenience copy.** They are pinned in
> `framework/resources/config/environment_config.json` under `tooling`, which is
> the single source of truth — the CI workflows and the setup probe both read it.
> If this table and the config ever disagree, **the config wins**, and
> `/kernel/domain-setup` will say so with both values.
>
> You do not have to install from this table at all. Step 6 probes your host and
> prints the exact commands for the tools your chosen setup actually needs — which
> for a remote or cloud device is only Node.

| Tool | Version | Verify | Expect |
|---|---|---|---|
| Python | 3.10+ | `python --version` | `Python 3.1x.x` |
| Node.js | **22+** | `node --version` | e.g. `v24.11.1` |
| Git | any | `git --version` | a version line |
| Appium | 3.7.0 | `appium --version` | `3.7.0` |

Node 22 is a hard floor, not a preference: `appium-mcp` — the discovery server
wired in `.mcp.json` — requires it. Appium itself runs on 20, so a Node 20 host
will run generated tests and then fail only when you try to discover anything.

## Step 1: Clone

```bash
git clone https://github.com/isagawa-qa/platform-mobile-apps.git
cd platform-mobile-apps
```

**Verify:** `ls framework/interfaces/mobile_interface.py` → the file exists.

## Step 2: Python environment

```bash
# macOS / Linux
python3 -m venv .venv && source .venv/bin/activate

# Windows
python -m venv .venv && .venv\Scripts\activate

pip install -r requirements.txt
```

**Verify:** `pip show Appium-Python-Client` → `Version: 6.0.6`.

## Step 3: Fetch the reference apps

The demo apps are **never committed** — neither carries a LICENSE, so no
redistribution right is granted. `apps/` is git-ignored except its README.

Release URLs and tags are in [`apps/README.md`](apps/README.md).

**Verify:** `ls apps/*.app apps/*.apk` → at least one build present.

## Step 4: Your host section

macOS can run both platforms. Windows runs Android locally and reaches iOS
through a remote Mac or a cloud device.

**You do not have to work out which applies to you.** `/kernel/domain-setup`
(Step 6) opens with a host capability probe: it detects the OS and the installed
tooling, reads `requires_host_os` from the environment config, and prints exactly
which platform-and-device location combinations this machine can run now, which need an
install, and which are impossible here. It loops until at least one is runnable.

The sections below are the install detail that probe will point you at. Read the
one it names rather than the one you assume.

---

## macOS host

### 4a.1 Xcode and command line tools
**Verify:** `xcodebuild -version` → `Xcode 16.x`

The version is deliberately loose: the CI picker caps the simulator runtime at
the active Xcode's major, because the *pairing* is what matters, not the
absolute version.

### 4a.2 An iOS 18 simulator
**Verify:** `xcrun simctl list runtimes` → a row containing `iOS 18.x`

### 4a.3 Appium and the XCUITest driver
```bash
npm install -g appium@3.7.0
appium driver install xcuitest@12.12.4
```
**Verify:** `appium driver list --installed` → `xcuitest@12.12.4`

### 4a.4 JDK 17 and the Android SDK
Only if you intend to run Android on the Mac. Follow the Windows preflight below
from step 4b.2 onward.

### 4a.5 Doctor
**Verify:** `appium driver doctor xcuitest` → zero *necessary* failures.
Optional-dependency warnings are fine.

### Running iOS locally, with no CI in the loop
Set `platforms.ios.device_location` to `local` (or leave `MOBILE_DEVICE_LOCATION_IOS` unset — it
defaults to `local`), then:
```bash
pytest -m ios --platform=ios
```
**Expect:** a session opens against your booted simulator. A Mac needs no CI for
any of this.

---

## Windows host

### 4b.1 iOS on Windows
There is no local Apple toolchain. Two supported routes:
- Set `platforms.ios.device_location` to `cloud` or `remote` and put credentials in `.env`.
- Or push to CI: `.github/workflows/ios-reference.yml` runs on a GitHub-hosted Mac.

**Verify:** `python -c "import json;d=json.load(open('framework/resources/config/environment_config.json'));print(d['platforms']['ios']['device_location'])"`
→ prints the device location expression.

### 4b.2 JDK 17
**Verify:** `java -version` → `openjdk version "17.x"`

### 4b.3 Android SDK command-line tools
**Verify:** `sdkmanager --version` → a version line

### 4b.4 Platform tools
```bash
sdkmanager "platform-tools" "platforms;android-34"
```
**Verify:** `adb version` → `Android Debug Bridge version 1.0.x`

### 4b.5 A system image with Google APIs
```bash
sdkmanager "system-images;android-34;google_apis;x86_64"
```
**Verify:** `sdkmanager --list_installed | grep google_apis` → the image is listed

A `google_apis` image is required, not the plain `default` one: the plain image
ships no Chrome, and the mobile-web lane needs a browser.

### 4b.6 Create an AVD
```bash
avdmanager create avd -n mobileqa_api34 -k "system-images;android-34;google_apis;x86_64"
```
**Verify:** `emulator -list-avds` → `mobileqa_api34`

### 4b.7 Confirm hardware acceleration
**Verify:** `emulator -accel-check` → `WHPX (10.0.x) is installed and usable`

On an AMD host with Hyper-V, WSL2 or Docker Desktop running, **WHPX is the only
accelerator that coexists**. HAXM does not support AMD, and AEHD requires the
hypervisor off, which would break WSL2 and Docker.

### 4b.8 Boot the emulator on the Windows host
```bash
emulator -avd mobileqa_api34
```
Run it on the host directly — **not** inside WSL or Docker. Google's own docs
forbid nested VM acceleration.

**Verify:** `adb devices` → one line reading `emulator-5554   device`

### 4b.9 Appium and the UiAutomator2 driver
```bash
npm install -g appium@3.7.0
appium driver install uiautomator2@8.7.0
```
**Verify:** `appium driver list --installed` → `uiautomator2@8.7.0`

### 4b.10 Start the Appium server
```bash
appium --port 4723 --log appium.log --log-level info
```
**Verify:** `curl -s http://127.0.0.1:4723/status` → JSON containing `"ready":true`

### 4b.11 Environment file
Copy `.env.example` to `.env` and fill the keys you need.
**Verify:** `ls .env` → the file exists. It is git-ignored and must stay so.

> **Android is currently deferred** by owner decision so the iOS path can be
> proven first. The preflight above is documented and correct; it has not yet
> been exercised end to end on this platform.

---

## Step 5: Verify setup

Run the env-repro probes before blaming any test. They are what separates an
environment failure from a code failure.

| Probe | Expect |
|---|---|
| `emulator -accel-check` | `WHPX ... is installed and usable` |
| `adb devices` | a line `emulator-5554   device` |
| `curl -s http://127.0.0.1:4723/status` | JSON containing `"ready":true` |
| `python -m pytest --fixtures -q` | lists `driver`, `config`, `device`, `mobile`, `artifacts_dir`, `test_users`, `workflow_data` |
| `npx appium-mcp@latest --help` | the MCP server resolves and runs (first run downloads it) |

### The discovery server

`.mcp.json` wires [`appium-mcp`](https://github.com/appium/appium-mcp), the Appium
project's own MCP server. It is what `/qa-workflow` step 4 drives to find elements
in your app. It is the mobile counterpart of the Playwright MCP server the Selenium
platform uses, and it plays the same role: **it discovers; it does not generate.**
Generated tests never go through it — they run through `tests/conftest.py` and
`MobileInterface`.

Two settings in `.mcp.json` are deliberate:

| Setting | Why |
|---|---|
| `AI_VISION_ENABLED: "false"` | Vision-based element finding can return a target that has no stable id, which cannot be traced back to a page source. The platform's evidence rule forbids writing such a locator. Hierarchy only. |
| `APPIUM_MCP_ON_CLIENT_DISCONNECT: "delete_all"` | Sessions are torn down when the client disconnects. On a paid device farm an orphaned session bills until it times out. |

**Android:** add `"ANDROID_HOME": "<your sdk path>"` to the `env` block. It is left
out because it is machine-specific and Android is not yet in scope.

**Driving a device that is not on this host** — the Windows-to-iOS case — is done by
passing `remoteServerUrl` to the `appium_session_management` tool when creating the
session. It is a tool argument, not an environment variable. Set
`REMOTE_SERVER_URL_ALLOW_REGEX` in `.mcp.json` if you want to restrict which
servers may be reached.

## Step 6: Run `/kernel/session-start`, then `/kernel/domain-setup`

**Both, in that order. Neither is optional.**

This repo ships pre-domain-setup: there is no generated protocol, no domain
hooks, no `.claude/lessons/lessons.md` and no `.claude/state/`. `domain-setup`
step 8 is what creates them.

`session-start` is not optional either — `universal-gate-enforcer.py` is a
PreToolUse hook on `Edit`, `Write` and `Bash`. With no `session_state.json` it
reads `{}` and **blocks your very first action** with `BLOCKED: Session not
started`. So the guarantee that makes this repo clean to ship is the same thing
that stops a fresh installer dead unless session-start runs first.

```
/kernel/session-start
/kernel/domain-setup
```

**Verify:** `.claude/protocols/<domain>-protocol.md` and
`.claude/lessons/lessons.md` both exist.

## Step 7: Run the reference suite

```bash
pytest -m ios --platform=ios        # macOS, or CI
pytest -m android --platform=android
```

**Expect:** Reference Flow 1 — log in, add a product to the cart, check out —
running as one test body.

## Next Steps

| Doc | Purpose |
|---|---|
| [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) | Extending the platform; the 5-layer contract in full |
| [`INTEGRATION.md`](INTEGRATION.md) | Adopting the platform in a consuming project |
| `/qa-workflow` | Describe a workflow in English, get Screens, Tasks, Roles and a test |

`/qa-workflow` is reachable **only after Step 6**. It reads the generated
protocol and lessons file, and blocks on them if they do not exist.

## Troubleshooting

**`BLOCKED: <something>` on your first command.** The kernel is telling you what
to invoke. Run the command it names — usually `/kernel/session-start`. Do not
edit state files to get past it.

**`error: externally-managed-environment` on macOS.** The system python is
Homebrew-managed under PEP 668. Use the venv from Step 2, or `actions/setup-python`
in CI.

**`emulator -accel-check` says WHPX is not usable.** Enable the Windows
Hypervisor Platform feature and reboot. If HAXM is installed, remove it — it
does not support AMD and conflicts with WHPX.

**iOS session times out waiting for WebDriverAgent.** WDA is compiled by
`xcodebuild` on first use; a cold machine outlasts Appium's default 60s wait.
The shipped iOS blocks already carry `appium:wdaLaunchTimeout: 600000` with two
retries. If you overrode it, put it back.
