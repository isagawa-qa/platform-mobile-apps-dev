<!-- SPDX-License-Identifier: MIT -->

# Step 5 Payload: Diagnostics and the Mobile Failure Map

**Purpose:** What to collect on a failure, and how to read it. Read before proposing any fix.

---

## Diagnostic Types

A mobile failure gives you less than a browser failure does. There is no console,
no network panel, and no DOM inspector. What you have:

| # | Type | How to get it |
|---|------|---------------|
| 1 | Error and stack trace | pytest output |
| 2 | Screenshot at failure | `tests/conftest.py` captures on failure; `artifacts/screenshots/` |
| 3 | Page source at failure | `artifacts/page_source/` — the tree as it actually was |
| 4 | Current context + context list | `driver.context`, `driver.contexts` |
| 5 | Element state | `is_element_displayed`, `is_element_enabled` |
| 6 | Device and session facts | platform, device name, OS version, device location, session id |
| 7 | Timing | how long the wait ran before it gave up |

**The page source at failure is the single most valuable artifact.** Diff it
against the Step 4 capture. If the id you targeted is absent from the failure
dump but present in the capture, the screen changed. If it is absent from both,
you targeted something that never existed.

---

## The Mobile Failure Map

| Symptom | Most likely cause | What to check FIRST |
|---------|-------------------|---------------------|
| `NoSuchElementException` on a locator that worked before | App updated and the id changed | Diff failure page source against the Step 4 capture |
| `NoSuchElementException` on a brand-new locator | The id was never real | grep the value against the captures — if absent, it was invented |
| Element found but tap does nothing | Wrong context, or an overlay | `driver.context`; look for a modal in the page source |
| Works on iOS, fails on Android | The locator dict has no android key, or the wrong one | Check the android capture exists; check `locator()` fell back to ios |
| Everything fails, session error | Simulator/emulator died or Appium restarted | Device reachability, Appium log |
| Passes alone, fails in a suite | State left behind by a previous test | `appium:noReset` and what the earlier test did |
| Timeout waiting for a screen | The transition is slower than the wait | Timing data; whether the screen appears at all in the dump |
| Web assertion fails in a hybrid app | Still in `NATIVE_APP` | Context list; switch before asserting |
| Exit code 5, "no tests ran" | Nothing collected | Test path, marker, class/function naming |

---

## Reading A Context Failure

Hybrid apps carry more than one context. A locator written for the native tree
cannot resolve while the driver is in a webview, and vice versa.

```
contexts: ['NATIVE_APP', 'WEBVIEW_com.example.app']
current:  'NATIVE_APP'
```

If the assertion targets web content and `current` is `NATIVE_APP`, the fix is a
context switch in the Screen Object, not a new locator. If the context list has
only `NATIVE_APP` when a webview was expected, the webview has not loaded yet —
that is a wait, not a locator problem.

---

## Before Proposing A Locator Fix

```
[ ] I diffed the failure page source against the Step 4 capture
[ ] The value I want to change TO appears verbatim in a capture
[ ] I can cite the capture file and line
[ ] I checked the context is the one the locator belongs to
[ ] I confirmed this is not a platform-key fallback picking the wrong value
```

If the replacement value is not in any capture, **do not propose it**. Recapture
the screen and propose from evidence. A locator fix sourced from reasoning
rather than a dump is how invented ids get into a suite — and they pass review
precisely because they look plausible.

---

## Flaky vs Broken

| Evidence | Verdict |
|----------|---------|
| Passes on retry, no code change | Flaky — record the timing, do not "fix" it silently |
| Same error signature twice | Broken — a real fix is needed |
| Different error each run | Environment instability — check device and Appium health |
| Fails only in CI | Device Location difference — compare the resolved capabilities |

A test that passes on retry is not a pass. Record it as flaky in the state file
so the pattern is visible when it happens again.

---

## G. HITL Triage Protocol (MANDATORY - NO AUTONOMOUS FIXES)

**CRITICAL: Agent MUST stop and ask on EVERY failure. No exceptions.**

**CHECKPOINT:** On ANY failure, invoke `/qa-on-failure` command FIRST.

This checkpoint provides the exact failure report format and response protocol. Do not skip this checkpoint.

### On Test Failure - STOP IMMEDIATELY

```
1. STOP - Do not attempt ANY fix
2. REPORT - Show exact failure:

   ===== TEST FAILED =====
   Test: [test name]
   Error: [exact error message]
   Location: [file:line]
   Device: [platform / device name / os version]
   Context: [NATIVE_APP or WEBVIEW_*]

   AI Analysis: [likely cause]

   HOW SHOULD WE PROCEED?
   1. Application Defect - Log it, stop workflow
   2. AI Proposes Fix - I'll show you what I'd change (you approve)
   3. Investigate - Show me diagnostic data
   4. You Fix - Tell me exactly what to change
   5. Skip - Continue without this test

3. WAIT - Do not proceed without user choice
```

### What "AI Proposes Fix" Means (Option 2):

**CHECKPOINT:** When user selects option 2, invoke `/qa-propose-fix` command.

```
User selects option 2
    │
    ▼
INVOKE /qa-propose-fix checkpoint
    │
    ▼
AI shows PROPOSED fix (does NOT apply it):
    "I would change:
     File: framework/screens/catalog/product_catalog_screen.py
     Line 34: ADD_BUTTON ios value 'AddToCart' → 'AddToCartButton'
     Evidence: tests/_state/captures/ios-product-detail.xml line 212

     Approve this fix? (yes/no)"
    │
    ├── User says YES → AI applies fix, re-runs test
    │
    └── User says NO → AI asks what to do instead
```

**A proposed locator change MUST cite the capture line it came from.** If no
capture supports the new value, the fix is a guess — recapture instead.

**AI NEVER applies fixes without explicit user approval.**

### Forbidden Behaviors:

- ❌ Attempting fix without showing user first
- ❌ Re-running test after autonomous fix
- ❌ Trying multiple solutions in a loop
- ❌ Assuming user wants AI to "just fix it"
- ❌ Making ANY code change without approval
- ❌ Changing a locator to a value no capture contains

### Triage Options (All Require User Choice):

| Option | Action | Requires Approval? |
|--------|--------|-------------------|
| **1. Application Defect** | Log to DEFECT_LOG.md, stop | YES (user confirms) |
| **2. AI Proposes Fix** | AI shows fix, waits for approval | YES (before applying) |
| **3. Investigate** | Show diagnostic data | YES (user requests) |
| **4. You Fix** | User describes the fix | YES (user provides) |
| **5. Skip** | Continue without this test | YES (user confirms) |

### Retry Policy:

| Scenario | Behavior |
|----------|----------|
| First failure | Full HITL - present all options |
| After approved fix | Re-run test, report result |
| Fix didn't work | HITL again - do NOT try another fix autonomously |
| Same error 3 times | Escalate - something fundamental is wrong |

---

*Return to `step-05.md`.*
