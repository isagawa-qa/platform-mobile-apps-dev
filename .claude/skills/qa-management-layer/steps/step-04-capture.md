<!-- SPDX-License-Identifier: MIT -->

# Step 4 Payload: Page-Source Capture and Id Extraction

**Purpose:** How discovery actually works on a device. Read before writing any locator.

---

## Why Capture At All

A browser gives you a DOM you can read and a snapshot tool that names elements
for you. A native app gives you neither. What it gives you is an accessibility
tree, dumped on demand, whose ids were chosen by the app's developers and are
frequently nothing like the visible text.

Two consequences drive this whole step:

1. **Ids cannot be guessed.** A button reading "Add To Cart" may carry the id
   `AddToCart`, `btn_add`, or nothing at all. You find out by looking.
2. **Ids are not shared between platforms.** The same screen in the same app
   commonly uses different ids on iOS and Android, because the two native
   toolkits set them independently.

So the rule is absolute: **capture first, then write the class.** A locator that
did not come from a capture is a guess wearing a constant's name.

---

## The Tool You Drive: `appium-mcp`

Discovery runs through the MCP server wired in `.mcp.json`, not through a script
you write. A script cannot explore: each Bash call is a new process, so the
session dies with it. The MCP server holds one live session across turns, which
is what makes look-then-decide possible at all.

Tool names, verbatim:

| Purpose | Tool |
|---------|------|
| Create / attach / list / delete a session | `appium_session_management` |
| Dump the accessibility tree | `appium_get_page_source` |
| Find an element | `appium_find_element` |
| Tap, swipe, scroll, drag | `appium_gesture` |
| Install / activate / terminate the app | `appium_app_lifecycle` |
| List or switch native ↔ webview | `appium_context` |

The server exposes more than these — list the client's tools to see the rest
rather than guessing a name.

**A device that is not on this host** is reached by passing `remoteServerUrl` to
`appium_session_management` when creating the session. It is a tool argument,
not an environment variable. This is the path for discovering an iOS app from a
Windows host: point it at a Mac on the network or a cloud device farm. CI is not
an option for discovery — you cannot look, decide, and tap inside one batch run.

**Vision-based finding stays off** (`AI_VISION_ENABLED: "false"` in `.mcp.json`).
It can hand back an element that has no stable id, and a locator that cannot be
traced to a dump is exactly what the evidence gate forbids. Hierarchy only.

---

## The Discovery Loop

Nothing is known in advance. Every target comes from the dump taken one step
earlier — that is what makes this work on an app the platform has never seen.

```
appium_session_management(action=create, ...)   ← app launches by capability
        │
        ▼
appium_get_page_source  ──►  read it; say in plain words what is on screen
        │
        ▼
the scenario's next step says what to do ("open the products tab")
        │
        ▼
match that intent against the labels IN THE DUMP YOU JUST TOOK
   → that gives you the id this app actually uses
   → appium_find_element / appium_gesture against that id
        │
        ▼
appium_get_page_source again  ──►  repeat until the flow is walked
```

Two rules keep the loop honest:

- **Never tap by coordinate.** A blind tap either misses or lands somewhere you
  did not intend, and you cannot tell which from the result. Where an id genuinely
  does not exist, use a typed predicate against text or class from the dump.
- **Never carry an id between apps.** An id discovered in one app says nothing
  about another. The loop is the product; the ids are per-app output.

---

## Saving The Evidence

A tool result is not evidence — it disappears with the conversation. Write every
dump to disk as you take it, because the gate greps files, not transcripts.

| Rule | Detail |
|------|--------|
| One file per screen per platform | `{platform}-{screen-slug}.xml` |
| Capture AFTER the screen settles | A capture mid-transition shows the previous screen |
| Capture after a gesture, not before | Ids that appear on scroll are absent until you scroll |
| Never edit a capture by hand | It is evidence; editing it destroys the only thing it is good for |

Captures live in `tests/_state/captures/` alongside `workflow_state.json`.

---

## Reading An iOS (XCUITest) Capture

The tree is XML of `XCUIElementType*` nodes. The attributes that matter:

| Attribute | Meaning | Maps to |
|-----------|---------|---------|
| `name` | the accessibility identifier | `AppiumBy.ACCESSIBILITY_ID` |
| `label` | what VoiceOver reads | `IOS_PREDICATE` on `label` |
| `value` | current value of a field | assertions |
| `type` | `XCUIElementTypeButton`, etc. | `IOS_CLASS_CHAIN` |
| `visible`, `enabled` | interactability | state checks |

```xml
<XCUIElementTypeButton type="XCUIElementTypeButton" name="Catalog-tab-item"
                       label="Catalog" visible="true" enabled="true" />
```

Here `name="Catalog-tab-item"` is the locator value; `label="Catalog"` is not.

---

## Reading An Android (UiAutomator2) Capture

Same idea, different attribute names:

| Attribute | Meaning | Maps to |
|-----------|---------|---------|
| `content-desc` | the accessibility identifier | `AppiumBy.ACCESSIBILITY_ID` |
| `resource-id` | the Android view id | `AppiumBy.ID` |
| `text` | visible text | `ANDROID_UIAUTOMATOR` on `text` |
| `class` | widget class | `AppiumBy.CLASS_NAME` |

`ACCESSIBILITY_ID` resolves to `name` on iOS and `content-desc` on Android. That
is why it is the preferred strategy: one strategy name, both platforms — but
still two different values, each from its own capture.

---

## Extracting Candidates

```python
import xml.etree.ElementTree as ET

tree = ET.parse(capture_path)
ids = {}
for node in tree.iter():
    key = node.get("name") or node.get("content-desc")
    if key:
        ids.setdefault(key, []).append(node.get("type") or node.get("class"))
```

Then judge each candidate:

| Signal | What it means | What to do |
|--------|---------------|------------|
| Appears once, descriptive | A good locator | Use it |
| Appears many times | A generic id on a repeated element | Select by index, not by id |
| Empty or missing | The element has no accessibility id | Fall back per the strategy order |
| Looks like visible text | May be the label, not the id | Confirm it is `name`/`content-desc` |

**The repeated-id trap is common and costly.** In a list of product tiles every
tile can carry the same id. There is then no per-item locator, and a
`PRODUCT_BY_NAME` constant cannot exist. Select by position instead, and say so
in a comment so the next reader does not go looking for the locator you "forgot".

---

## Locator Strategy Order

1. `ACCESSIBILITY_ID` — first choice, works on both platforms
2. `IOS_PREDICATE` / `ANDROID_UIAUTOMATOR` — typed fallbacks when no id exists
3. `IOS_CLASS_CHAIN` — hierarchy when predicate is not enough
4. XPath — last resort only; brittle and slow on both platforms

---

## Writing The Locator Constant

```python
SCREEN_ROOT = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Catalog-screen")}
CATALOG_TAB = {"ios": (AppiumBy.ACCESSIBILITY_ID, "Catalog-tab-item")}

def locator(self, name: str):
    """Resolve a platform-keyed locator constant for the current platform."""
    entry = getattr(self, name)
    return entry.get(self.mobile.platform) or entry["ios"]
```

| Rule | Why |
|------|-----|
| One key per platform you captured | A key you did not capture is an unverified claim |
| No `"default"` key unless the id is genuinely shared AND both captures prove it | Otherwise it asserts an id on a platform nobody looked at |
| Comment the capture each value came from | The next person needs to re-verify without re-discovering |

---

## Before You Leave This Step

```
FOR EACH locator constant written:
  [ ] its literal value appears verbatim in a capture on disk
  [ ] the capture is named in a comment or in workflow_state.json
  [ ] every platform key present has its own capture
  [ ] no "default" key was added on the strength of one platform
```

If any box is unchecked, the Screen Object is not finished — regardless of
whether the test happens to pass.

---

*Return to `step-04.md` § D.4 to build the modules.*
