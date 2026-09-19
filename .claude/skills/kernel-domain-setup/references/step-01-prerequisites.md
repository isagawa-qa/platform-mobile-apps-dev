# Step 1: Prerequisites

Before domain setup, verify all dependencies are installed and configured.

## 1.0 Host Capability Probe — RUN THIS FIRST

**A mobile platform is gated by the host OS in a way a web platform is not.**
Chrome runs everywhere; iOS tooling exists only on macOS. So which targets this
machine can test is a fact to be *computed*, not a section for the user to pick
by eye. Compute it before anything is installed, not at the first test run.

This is a **loop**. Probe, report, wait for the user to act, then probe again.
Never proceed on an unprobed host and never assume an install succeeded.

### Detect

| Fact | How |
|------|-----|
| Host OS | `python -c "import sys; print(sys.platform)"` → `darwin`, `win32`, `linux` |
| Node | `node --version` (22+ required by `appium-mcp`) |
| Java | `java -version` |
| Appium | `appium --version` |
| Android SDK | `ANDROID_HOME` set, and `adb` / `emulator` on PATH |
| iOS tooling | `xcrun simctl list runtimes` — macOS only, absent elsewhere |

### Derive

Read `framework/resources/config/environment_config.json`. For every
`platforms[*]` and every venue block inside it:

```
IF venue has requires_host_os AND it != host_os   -> IMPOSSIBLE on this host
ELSE IF the tooling that venue implies is present -> RUNNABLE NOW
ELSE                                              -> REACHABLE AFTER INSTALL
```

Read `requires_host_os` from the config. Do not hardcode which platform needs
which OS — the config is the authority and it can gain venues.

### Report

```
HOST CAPABILITY — win32

RUNNABLE NOW
  (none)

REACHABLE AFTER INSTALL
  android / local    needs: JDK 17, Android SDK, an AVD, Appium + UiAutomator2

IMPOSSIBLE ON THIS HOST
  ios / local        requires darwin — iOS tooling does not exist off macOS
  ios / ci           requires darwin — runs on the macos-15 runner, not here

REACHABLE WITHOUT LOCAL TOOLING
  ios / remote       an Appium server on a machine that has Xcode
  ios / cloud        a device-farm account
```

### Loop

| Outcome | Action |
|---------|--------|
| At least one venue RUNNABLE NOW | Record it to state (below), continue to 1.1 |
| None runnable, some reachable after install | **STOP.** Give the install steps for the cheapest path. Wait. On "continue", **re-probe** — do not trust that it worked |
| None runnable and none reachable locally | **STOP.** This host cannot test locally at all. Name the `remote` and `cloud` routes and what each needs |

Record the outcome so later steps and the generated protocol can use it, merging
into `.claude/state/session_state.json`:

```json
{
  "host_capability": {
    "host_os": "win32",
    "runnable_now": [],
    "reachable_after_install": ["android/local"],
    "impossible_here": ["ios/local", "ios/ci"],
    "probed_at": "[ISO-8601]"
  }
}
```

Step 8 writes the protocol. A protocol that names a venue this host cannot run is
a defect — the protocol describes *this* installation, not the product in general.

---

## MCP Servers (if applicable)

Check if configured in `.mcp.json` at the repository root. (Claude Code reads
`.mcp.json` at the project root; `.claude/mcp.json` is not loaded.)

```json
{
  "mcpServers": {
    "[server-name]": {
      "command": "...",
      "args": ["..."]
    }
  }
}
```

**If not configured:**
1. Create/update `.claude/mcp.json` with required config
2. Set restart state (see below)
3. Stop and wait for restart

## Dependencies

Check for dependency files and install:

| File | Action |
|------|--------|
| `package.json` | `npm install` |
| `requirements.txt` | `pip install -r requirements.txt` |
| `go.mod` | `go mod download` |
| `Cargo.toml` | `cargo build` |

## Settings

Verify `.claude/settings.local.json` has MCP servers enabled (if using MCP):

```json
{
  "enableAllProjectMcpServers": true
}
```

## Checklist

| Dependency | Check | Action if Missing |
|------------|-------|-------------------|
| **Host capability** | **§ 1.0 probe recorded in state** | **Report, wait, RE-PROBE — loop until a venue is runnable** |
| MCP servers | `.mcp.json` at repo root configured | Add config → restart |
| Dependencies | Package manager files exist | Install dependencies |
| MCP enabled | settings.local.json configured | Add enableAllProjectMcpServers |

The host probe comes first. Installing dependencies for a venue this host can
never run wastes the user's time and ends in a runtime failure that looks like a
platform defect.

---

## Restart Flow (Integration with Session-Start Loop)

If ANY MCP configuration changed, restart is required. MCP servers load at Claude Code startup.

### Step 1a: Set Restart State

Create/update `.claude/state/session_state.json`:

```json
{
  "session_started": true,
  "domain": "[domain]",
  "needs_restart": true,
  "resume_after_restart": "domain-setup",
  "resume_step": 2,
  "timestamp": "[ISO-8601]"
}
```

### Step 1b: Report and Stop

```
PREREQUISITES: Restart Required

Changed:
- [list what was configured/changed]

State saved. After restart, domain-setup will resume from Step 2.

⚠️  RESTART REQUIRED

1. Restart Claude Code now
2. Say "continue"
3. /kernel/session-start will read state and resume

Waiting for restart...
```

**STOP. Do not proceed until user restarts.**

### Step 1c: After Restart (Handled by session-start)

When user says "continue":
1. `/kernel/session-start` reads state
2. Sees `needs_restart: true` → clears flag
3. Sees `resume_after_restart: "domain-setup"`
4. Invokes `/kernel/domain-setup`
5. Domain-setup sees `resume_step: 2` → skips to Step 2

---

## No Restart Needed

If all dependencies already configured:

```
PREREQUISITES: All configured

✓ Dependencies installed
✓ MCP configured (if applicable)
✓ Settings configured

Proceeding to Step 2...
```

Continue to Step 2 immediately.
