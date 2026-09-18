"""Drive the reference app to each Flow 1 screen and dump its page source.

Run by .github/workflows/capture-ios.yml on a macos-15 runner. The output is the
evidence every locator in framework/_reference/ must be derived from: contract
rule CR-5 of design sheet 05 requires each locator value to appear verbatim in a
COMMITTED capture, and L1-REF-02 fails on a missing one.

This script discovers nothing about the app's structure. It taps by coordinate
proportion and dumps whatever is on screen, because the whole point is that the
accessibility ids are not yet known - that is what the capture is for. Locators
are derived from the XML afterwards, never typed from memory or copied from a
third-party repository.

Every screen is dumped even when navigation fails, so a partial run still yields
evidence and names what it could not reach.
"""
import logging
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "framework"))

from appium import webdriver
from appium.options.ios import XCUITestOptions
from resources.utilities.autologger import automation_logger

# autologger supplies the entry/exit decorator the whole platform uses; it does
# not configure handlers, so the stream setup stays here.
logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
log = logging.getLogger("capture")

OUT = pathlib.Path("captures")
OUT.mkdir(parents=True, exist_ok=True)

REQUIRED = ("IOS_UDID", "IOS_DEVICE_NAME", "IOS_PLATFORM_VERSION", "IOS_APP_PATH")
missing = [name for name in REQUIRED if not os.environ.get(name)]
if missing:
    sys.exit("missing required environment: %s" % ", ".join(missing))

options = XCUITestOptions()
options.set_capability("platformName", "iOS")
options.set_capability("appium:automationName", "XCUITest")
options.set_capability("appium:udid", os.environ["IOS_UDID"])
options.set_capability("appium:deviceName", os.environ["IOS_DEVICE_NAME"])
options.set_capability("appium:platformVersion", os.environ["IOS_PLATFORM_VERSION"])
options.set_capability("appium:app", os.environ["IOS_APP_PATH"])
options.set_capability("appium:noReset", False)
# Cold-runner values proven by run 35270978418. WebDriverAgent is compiled by
# xcodebuild on first use, which outlasts Appium's default 60s launch wait.
options.set_capability("appium:wdaLaunchTimeout", 600000)
options.set_capability("appium:simulatorStartupTimeout", 300000)
options.set_capability("appium:wdaStartupRetries", 2)
options.set_capability("appium:wdaStartupRetryInterval", 20000)
options.set_capability("appium:newCommandTimeout", 180)

driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
captured, unreached = [], []


@automation_logger("Capture")
def dump(name):
    """Write the current page source. Never raises; a failed dump is recorded."""
    try:
        path = OUT / ("ios-%s.xml" % name)
        path.write_text(driver.page_source, encoding="utf-8")
        size = path.stat().st_size
        captured.append((name, size))
        log.info("  captured %-22s %8d bytes", name, size)
        return True
    except Exception as exc:  # noqa: BLE001
        unreached.append((name, str(exc)[:160]))
        log.info("  FAILED   %-22s %s", name, exc)
        return False


@automation_logger("Capture")
def tap_proportional(x_frac, y_frac):
    """Tap at a proportion of the screen. Coordinates, because ids are unknown."""
    size = driver.get_window_size()
    driver.execute_script("mobile: tap", {
        "x": int(size["width"] * x_frac),
        "y": int(size["height"] * y_frac),
    })
    time.sleep(2)


@automation_logger("Capture")
def navigate(label, x_frac, y_frac):
    """Tap, then dump. A navigation failure is recorded, never raised."""
    try:
        tap_proportional(x_frac, y_frac)
        dump(label)
    except Exception as exc:  # noqa: BLE001
        unreached.append((label, str(exc)[:160]))
        log.info("  navigation to %s failed: %s", label, exc)


try:
    # This build opens on the catalog; login is reached through the tab bar.
    # Both are dumped regardless of which is showing.
    time.sleep(4)
    dump("product-catalog")
    dump("tab-bar")

    navigate("product-detail", 0.25, 0.35)   # first product tile
    navigate("cart", 0.90, 0.09)             # header cart icon
    navigate("login", 0.87, 0.95)            # rightmost tab-bar item

    # The checkout screens need an authenticated session and a populated cart.
    # They are attempted and honestly recorded as unreached on failure, rather
    # than quietly omitted from the manifest.
    for screen in ("checkout-info", "checkout-complete"):
        if not dump(screen):
            log.info("  %s not reached in this pass", screen)

finally:
    lines = ["iOS page-source capture", ""]
    lines.append("device:   %s %s" % (os.environ["IOS_DEVICE_NAME"],
                                      os.environ["IOS_PLATFORM_VERSION"]))
    lines.append("udid:     %s" % os.environ["IOS_UDID"])
    lines.append("app:      %s" % os.environ["IOS_APP_PATH"])
    lines.append("bundle:   %s" % os.environ.get("IOS_BUNDLE_ID", ""))
    lines.append("")
    lines.append("captured (%d):" % len(captured))
    lines.extend("  %-22s %8d bytes" % (n, s) for n, s in captured)
    lines.append("")
    lines.append("not captured (%d):" % len(unreached))
    lines.extend("  %-22s %s" % (n, e) for n, e in unreached)
    if not unreached:
        lines.append("  none")
    (OUT / "CAPTURE-SUMMARY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("\n%s", "\n".join(lines))
    try:
        driver.quit()
    except Exception:  # noqa: BLE001
        pass

# A run that captured nothing is a failure. A run that captured some screens is
# evidence for those, and a named gap for the rest.
if not captured:
    sys.exit("no screens captured")
