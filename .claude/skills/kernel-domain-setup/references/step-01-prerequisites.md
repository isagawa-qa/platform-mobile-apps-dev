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

**Nothing about the toolchain is written here.** `environment_config.json` is the
authority — read it and probe what it names. Anything restated in this file would
be a second copy to drift.

The host OS is the one fact the config does not hold:

```
host_os = python -c "import sys; print(sys.platform)"   ->  darwin | win32 | linux
```

For everything else, walk `tooling`. Each entry carries its own probe, and either
a `pin` (an exact version) or a `min` (a floor):

```
FOR name, spec IN tooling:
    IF spec.host_os AND spec.host_os != host_os:  skip - not applicable here
    IF spec.env AND that variable is unset:       MISSING
    run spec.probe
      not found            -> MISSING
      found, spec.pin      -> compare exactly;  mismatch -> WRONG VERSION
      found, spec.min      -> compare floor;    below    -> WRONG VERSION
      otherwise            -> OK

FOR name, spec IN tooling.drivers:
    `appium driver list --installed` -> compare against spec.pin
```

**A wrong version is not "present".** Reporting a tool as OK on presence alone
lets setup pass and the failure surface later as something that looks like a
platform defect. Report `WRONG VERSION` with both values and the install command,
which is `spec.install` with `{pin}` substituted — never a version typed here.

### Derive

For every `platforms[*]` and every device location block inside it:

```
IF the block has requires_host_os AND it != host_os  -> IMPOSSIBLE on this host
ELSE IF every tool in the block's `requires` is OK   -> RUNNABLE NOW
ELSE                                                 -> REACHABLE AFTER INSTALL
                                                        (list the MISSING and
                                                         WRONG VERSION entries)
```

`requires` names entries in `tooling`; `driver:x` means `tooling.drivers.x`.
Both it and `requires_host_os` come from the config, so a new device location or
a changed pin is picked up without editing this file.

Note what `requires` makes visible: `remote` and `cloud` need only `node`. The
heavy toolchain lives where the device is, not on this machine — which is the
whole reason those locations exist for a host that cannot run the target.

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
| At least one device location RUNNABLE NOW | Record it to state (below), continue to 1.1 |
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

Step 8 writes the protocol. A protocol that names a device location this host cannot run is
a defect — the protocol describes *this* installation, not the product in general.

### Ask — only what the probe cannot answer

Everything above is detected. **Ask only what is genuinely the user's and
genuinely ambiguous.** A question you could have answered by looking reads as the
tool not knowing its own environment.

Apply that test to each thing setup needs to know and ask whatever survives it.
Do not aim for a fixed number of questions — the count falls out of how much this
particular host and repo already answer, and it is often zero. The two below are
the ones that survive today; a new dimension in the config adds its own.

**Which do you test?** Skip it if only one target has any viable device location,
or if `apps/` contains artifacts for exactly one platform (`.ipa`/`.app` → iOS,
`.apk` → Android). Otherwise ask, offering only targets with a viable location.

**Which device location, per chosen target?** Skip it whenever exactly one is
viable — state the choice instead of asking it. Ask only when two or more are.

Build the options from `environment_config.json`, never from a list kept here.
A question set maintained in parallel with the config will disagree with it, and
then setup offers device locations that do not exist.

Ask one at a time, and give each option what it costs, not just its name:

```
iOS on this host can run two ways:

  remote  — an Appium server on a Mac you can reach.
            Free if you have one. Fast, interactive.
  cloud   — a device-farm account.
            Real devices, works from anywhere, costs per minute.

You have no Mac configured, so I'd suggest cloud.  Which?
```

### Record

Write the answer to `.env` — `MOBILE_DEVICE_LOCATION_IOS` / `MOBILE_DEVICE_LOCATION_ANDROID`. These
already drive `platforms[*].device_location` in the config, so nothing new is introduced
and the choice survives the session.

**If the variable is already set, do not ask at all.** Setting it directly is the
supported override and the escape hatch if this step ever misbehaves: setup must
never be the only way to configure the platform.

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
1. Create/update `.mcp.json` at the repository root with required config
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
| **Host capability** | **§ 1.0 probe recorded in state** | **Report, wait, RE-PROBE — loop until a device location is runnable** |
| MCP servers | `.mcp.json` at repo root configured | Add config → restart |
| Dependencies | Package manager files exist | Install dependencies |
| MCP enabled | settings.local.json configured | Add enableAllProjectMcpServers |

The host probe comes first. Installing dependencies for a device location this host can
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
