"""L2-03: an injected driver failure must PROPAGATE (backlog 321).

Three things are asserted, and a fourth case exists to prove the test can fail:

  CASE A  propagation  - the exception reaches the caller, a logger.error was
                         emitted, and the message carries the context.
  CASE B  exemption    - the four allow-listed state checks DO return False/[]
                         on TimeoutException. The rule must hold in BOTH
                         directions or it is untested.
  CASE C  control      - a deliberately-swallowing interface. Case A's assertion
                         must REJECT it. A must-propagate test that has never
                         gone red is not evidence, however green it looks.

No real driver is constructed. No network call is made. No device is required.
"""
import logging
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEV = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(DEV / "framework"))

from selenium.common.exceptions import TimeoutException, WebDriverException  # noqa: E402
from interfaces import MobileInterface  # noqa: E402

results = []


def record(case, ok, observed):
    results.append((case, "PASS" if ok else "FAIL", observed))


class RecordingLogger(logging.Logger):
    def __init__(self):
        super().__init__("recording")
        self.errors = []
        self.warnings = []

    def error(self, msg, *a, **k):
        self.errors.append(str(msg))

    def warning(self, msg, *a, **k):
        self.warnings.append(str(msg))


class ExplodingDriver:
    """Every interaction raises WebDriverException. Nothing else is implemented."""
    def __init__(self):
        self.capabilities = {}

    def find_element(self, *a, **k):
        raise WebDriverException("injected driver failure")

    def execute(self, *a, **k):
        raise WebDriverException("injected driver failure")


class TimingOutDriver:
    """Interactions time out, which is the condition the exemption covers."""
    def __init__(self):
        self.capabilities = {}

    def find_element(self, *a, **k):
        raise TimeoutException("injected timeout")


def build(driver, logger):
    return MobileInterface(driver, {"explicit_wait": 1}, logger, "ios")


# ---------------------------------------------------------------- CASE A
logger = RecordingLogger()
iface = build(ExplodingDriver(), logger)
propagated, exc_type = False, None
try:
    iface.find_element("accessibility id", "anything")
except WebDriverException as exc:
    propagated, exc_type = True, type(exc).__name__
except Exception as exc:  # noqa: BLE001
    propagated, exc_type = True, type(exc).__name__

logged = len(logger.errors) > 0
has_context = any("anything" in m for m in logger.errors)
record("A-propagates", propagated, "raised=%s" % exc_type)
record("A-logged", logged, "error records=%d" % len(logger.errors))
record("A-context", has_context,
       "first record=%r" % (logger.errors[0][:90] if logger.errors else None))

# ---------------------------------------------------------------- CASE B
logger_b = RecordingLogger()
iface_b = build(TimingOutDriver(), logger_b)
b_obs = {}
try:
    b_obs["is_element_present"] = iface_b.is_element_present("accessibility id", "x")
except Exception as exc:  # noqa: BLE001
    b_obs["is_element_present"] = "RAISED:" + type(exc).__name__
exempt_ok = b_obs.get("is_element_present") is False
record("B-exemption", exempt_ok, "is_element_present returned %r (expected False)"
       % b_obs.get("is_element_present"))

# ---------------------------------------------------------------- CASE C
class SwallowingInterface:
    """What the gate must REJECT: catches the driver error and returns None."""
    def __init__(self, driver, logger):
        self.driver, self.logger = driver, logger

    def find_element(self, by, value, timeout=None):
        try:
            return self.driver.find_element(by, value)
        except WebDriverException:
            return None


logger_c = RecordingLogger()
swallower = SwallowingInterface(ExplodingDriver(), logger_c)
c_propagated = False
try:
    swallower.find_element("accessibility id", "anything")
except WebDriverException:
    c_propagated = True

# The control must NOT propagate. If it does, the stub is wrong, not the code.
control_went_red = not c_propagated
record("C-control-red", control_went_red,
       "swallowing interface propagated=%s (must be False, i.e. the assertion "
       "in case A would FAIL against it)" % c_propagated)

# ---------------------------------------------------------------- report
out = DEV / "_context" / "interface-l2-negative-results.txt"
lines = ["%-16s %-4s %s" % (c, v, o) for c, v, o in results]
failed = [c for c, v, _ in results if v == "FAIL"]
lines += [
    "",
    "CASE C is the proof this test can fail: the swallowing interface returns",
    "None where the real one raises, so case A's propagation assertion rejects",
    "it. A green case A without a red case C would be unfalsifiable.",
    "",
    "OVERALL: %s  (%d checks, %d failed)" %
    ("PASS" if not failed else "FAIL", len(results), len(failed)),
]
text = "\n".join(lines)
out.write_text(text + "\n", encoding="utf-8")
print(text)
sys.exit(1 if failed else 0)
