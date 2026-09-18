# Page-source captures — provenance

Contract rule CR-5 of design sheet 05: **every locator value must appear verbatim
in a committed capture.** No id is typed from memory, inferred from a third-party
repository, or carried over from an earlier inventory without re-verification.

## The run

| | |
|---|---|
| Workflow | `.github/workflows/capture-ios.yml` |
| Run id | **35327677124** — `conclusion: success`, verified against the GitHub API |
| Commit | `a32a8af` |
| Runner | `macos-15` |
| Device | iPhone 16 Pro, iOS 18.6 |
| UDID | `7FF9581C-A82C-472C-B005-492B077D1038` |
| App | `My Demo App.app`, bundle `com.saucelabs.mydemo.app.ios` |
| Release | `saucelabs/my-demo-app-ios` tag **2.2.2**, asset `SauceLabs-Demo-App.Simulator.XCUITest.zip` |
| Captured | 2026-09-18 |

## What is here — three screens, not seven

The capture script wrote seven files. **Only three are distinct page sources.**
The other four are byte-identical duplicates: the coordinate taps did not reach
the screens they were aimed at, so the same source was dumped again under a
different name.

| File | Screen | Confirmed by |
|---|---|---|
| `ios-catalog.xml` | Product catalog | `Catalog-screen`, `ProductItem`, `Product Name`, `Product Price` |
| `ios-product-detail.xml` | Product detail | `ProductDetails-screen`, `Sauce Labs Backpack - Black`, colour swatches, `AddPlus Icons` |
| `ios-menu.xml` | The navigation drawer | `Webview-menu-item`, `QrCodeScanner-menu-item`, `GeoLocation-menu-item`, `About-menu-item` |

The duplicates were **discarded rather than committed under misleading names.** A
file called `ios-cart.xml` that actually contains the product-detail screen is
worse than no file: every locator derived from it would be wrong and would appear
to have provenance.

The script's own summary reported "captured (7)", which was true about files
written and false about screens reached. It counted outputs rather than proving
the property — the shape this project keeps hitting. Deduplicating by content
hash is what surfaced it.

## What is NOT here, and what it blocks

| Screen | Status | Consequence |
|---|---|---|
| Cart (populated) | **not captured** | `CartScreen` locators cannot be written; `is_item_in_cart` has no evidence |
| Login | **not captured** | `LoginScreen` locators cannot be written |
| Checkout info | **not captured** | `CheckoutInfoScreen` blocked |
| Checkout complete | **not captured** | `CheckoutCompleteScreen` blocked; `is_order_complete_displayed` has no evidence |

Reaching those four needs real navigation rather than proportional taps: log in,
add a product, open the cart, and walk the checkout. That in turn needs the ids
from the screens above, which is why this capture is still progress — the catalog
and detail ids are now evidenced, and the menu gives the route to login.

## What this capture already settles

The 24 ids in `design/05a-reference-locators.md` were parsed from a page source
that no longer existed, making every one of them *sourced but unverifiable*. The
catalog ids in that inventory are now **confirmed against a live capture**:
`Catalog-screen`, `AppLogo Icons`, `AppTitle Icons`, `title`, `ProductItem`,
`Product Image`, `Product Name`, `Product Price`, `StarSelected Icons`,
`StarUnSelected Icons` all appear verbatim in `ios-catalog.xml`.

## iOS only

Android is deferred by owner decision (2026-09-18). **No locator may carry a
`default` key** on this evidence: `default` claims an id is shared across both
platforms, and there is no Android capture to support that. Every locator gets an
explicit `ios` key until an Android capture shows the same string.
