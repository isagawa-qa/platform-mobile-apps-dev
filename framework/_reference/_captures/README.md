# Reference captures

Page sources for the screens in `../screens/`. **Every locator id in those files
appears verbatim in a capture here.** No id is typed from memory, and no id is
carried over from another platform because it "looks the same".

This directory is the evidence, not a convenience. A capture that is not
committed cannot be checked by the next person, so a CI run id is not a
substitute — build artifacts expire.

## What is here

| File | Platform | Screen | Source |
|---|---|---|---|
| `android-catalog.xml` | Android | Product catalog | emulator-5554, API 34 (google_apis, x86_64), UiAutomator2 8.7.0, app `com.saucelabs.mydemoapp.android` |
| `android-product-detail.xml` | Android | Product detail | same session, after tapping tile index 0 |

## What is missing

**There is no iOS capture in this directory.** The iOS ids in `../screens/` were
read from GitHub Actions run `35327677124` (iPhone 16 Pro / iOS 18.6) and are
correct, but that run's artifacts are not committed here and will expire. Until
an iOS capture lands, the iOS half of these screens rests on a citation rather
than on evidence in the repo, which is exactly the gap this directory exists to
close. Capture it on the next Mac run and drop it in as `ios-catalog.xml` and
`ios-product-detail.xml`.

The Android captures cover **browse and open a product** only. There is no
Android capture of the cart or the tab bar, which is why `cart_screen.py` and
`tab_bar_screen.py` carry no `"android"` key and `locator()` raises if an Android
run reaches them.

## How these were taken

Through the `appium-mcp` server wired in `.mcp.json` — `appium_get_page_source`
against a live session, written to disk unmodified. They are raw driver output:
do not hand-edit them, or they stop being evidence. To refresh one, take a new
capture and replace the file wholesale.

## Reading a capture

The two platforms label the same concept differently, which is the whole reason
locators are keyed by platform:

| Concept | iOS (XCUITest) | Android (UiAutomator2) |
|---|---|---|
| Accessibility id | `name=` | `content-desc=` |
| Resource id | — | `resource-id=` |
| Rendered | `visible=` | `displayed=` |

Both `name=` and `content-desc=` map to `AppiumBy.ACCESSIBILITY_ID`.
`resource-id=` maps to `AppiumBy.ID` and is Android-only.

Two traps these captures actually contain, both documented at the locators that
hit them:

1. **An element in the tree is not necessarily on screen.** Nodes appear with
   `visible="false"` / `displayed="false"`. Presence is not display — which is
   why the state-check methods use `is_element_displayed`, not a find.
2. **A resource-id can be reused across screens.** `productTV` is the heading
   "Products" on the catalog and the product's name on the detail screen. An
   `AppiumBy.ID` lookup for it succeeds on both and means different things, so
   it is only safe once the screen is known.
