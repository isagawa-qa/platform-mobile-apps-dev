<!-- SPDX-License-Identifier: MIT -->

# Gate Contract Payload: HITL and MobileInterface-First

**Purpose:** The two rules that override everything else in this skill.

> Index: `gate-contract.md`

---

## HITL Protocol (MANDATORY - NO EXCEPTIONS)

**Human-In-The-Loop is NOT optional. Agent MUST stop and ask.**

### On ANY Failure:

```
1. STOP IMMEDIATELY
   - Do NOT attempt autonomous fixes
   - Do NOT loop through solutions
   - Do NOT try "one more thing"

2. REPORT to user:
   "FAILURE at Step [N]: [brief description]

   Error: [exact message]
   Location: [file:line or screen]

   HOW SHOULD WE PROCEED?
   1. I'll fix it - tell me what to change
   2. You investigate - show me more context
   3. Skip this - continue without it
   4. Abort - stop workflow entirely"

3. WAIT for user response
   - Do NOT proceed without explicit user input
   - Do NOT assume user wants you to try fixes

4. ONLY THEN proceed based on user choice
```

### What Agent MUST NOT Do:

- ❌ Loop through multiple fix attempts without asking
- ❌ Try alternate solutions autonomously
- ❌ Assume it knows the right fix
- ❌ Continue past failures hoping they resolve
- ❌ Make more than ONE fix attempt before asking

### Why This Matters:

Pair programming means USER decides direction. Agent executes.
When agent loops autonomously, it's not pair programming - it's solo coding.

---

## MobileInterface Methods First (MANDATORY)

**Before writing ANY interaction logic in a Screen Object:**

```
1. CHECK: Does MobileInterface already have this method?

2. IF YES: Use it directly
   - self.mobile.wait_for_element_visible(*self.locator("NAME"))
   - NOT: custom polling loops

3. IF NO: STOP and ask user:
   "Need MobileInterface method: [description]

   Example: wait_for_toast(text, timeout)

   Should I add this to MobileInterface?"

4. WAIT for user approval before:
   - Creating workaround code
   - Using time.sleep()
   - Writing manual polling loops
```

**Confirm every name with `def <name>` in
`framework/interfaces/mobile_interface.py` before you use it. Never trust a
method name from memory, from this document, or from the Selenium platform.**
The list below was accurate when written and is a starting point for the grep,
not a substitute for it.

| Group | Methods |
|-------|---------|
| Find | `find_element`, `find_elements`, `is_element_present`, `is_element_displayed`, `is_element_clickable` |
| Wait | `wait_for_element_visible`, `wait_for_element_invisible`, `wait_for_text_in_element`, `wait_for_url_contains`, `wait_for_context` |
| Act | `click`, `type`, `tap`, `long_press`, `swipe`, `drag_and_drop`, `pinch_open`, `pinch_close` |
| Scroll | `scroll_to_element`, `scroll_to_bottom`, `scroll_to_top`, `scroll_until_visible` |
| Read | `get_text`, `get_attribute`, `get_page_source`, `get_current_url`, `get_page_title`, `take_screenshot` |
| Context | `switch_to_context`, `get_contexts`, `get_current_context`, `switch_to_webview`, `switch_to_native`, `switch_to_frame`, `switch_to_default_content` |
| App | `activate_app`, `terminate_app`, `install_app`, `remove_app`, `query_app_state` |
| Web-ish | `navigate_to`, `refresh_page`, `go_back`, `go_forward`, `select_by_text`, `select_by_value`, `get_select_options`, `execute_script` |

The "Web-ish" group exists for `-web` platforms and webview contexts. In a
native context there is no URL to navigate to and no HTML `<select>` — reaching
for those there is a sign the flow was modelled as a web page.

### Forbidden Patterns:

```python
# ❌ NEVER do this in a Screen Object:
import time
while not self.mobile.is_element_displayed(*self.locator("BANNER")):
    time.sleep(0.5)          # NO - ask for a MobileInterface method instead

# ✓ CORRECT - use the existing method:
self.mobile.wait_for_element_visible(*self.locator("BANNER"))

# ❌ NEVER touch the driver above the Interface layer:
self.mobile.driver.find_element(...)   # NO
el.click()                             # NO - a raw WebElement call

# ❌ NEVER add an alias for a method that already exists:
def enter_text(self, by, value, text):
    self.type(by, value, text)         # NO - call type() from the Screen
```

### Why This Matters:

- MobileInterface is the single source of device interaction patterns
- Custom workarounds create inconsistency and technical debt
- If the Interface is missing a method, adding it benefits ALL future tests
- A raw driver call above the Interface breaks the layer boundary the whole
  platform is built on, and it is invisible to anyone reading the test

---

## The Two Together

Both rules exist for the same reason: **the agent does not get to decide
alone.** HITL puts the user in charge of direction. MobileInterface-first puts
the platform in charge of mechanism. An agent that respects neither will produce
a suite that works once, on one machine, and cannot be maintained by anyone
else.

---

*Return to `gate-contract.md`.*
