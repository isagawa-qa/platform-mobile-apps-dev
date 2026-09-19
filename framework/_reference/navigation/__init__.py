"""
Navigation - per-platform Screen Objects, chosen once at construction.

Every other Screen in this reference is shared: the platforms show the same
thing with different ids, so one class carries a platform-keyed locator for
each. Navigation is the exception. iOS has a persistent bottom tab bar;
Android has a header whose catalog link is inside a drawer. Reaching the
catalog is one tap on iOS and two on Android - a difference in the SEQUENCE
of actions, which a locator cannot express.

`navigation_for()` resolves the right class from the session's platform. It is
the ONLY place in this reference that reads `mobile.platform` to decide
behaviour, and it does so once, when a Task is constructed. Tasks, Roles and
Tests then call the same method names and never branch.
"""

from interfaces.mobile_interface import MobileInterface
from _reference.navigation.ios_navigation_screen import IOSNavigationScreen
from _reference.navigation.android_navigation_screen import AndroidNavigationScreen

__all__ = ["IOSNavigationScreen", "AndroidNavigationScreen", "navigation_for"]

_BY_PLATFORM = {
    "ios": IOSNavigationScreen,
    "android": AndroidNavigationScreen,
}


def navigation_for(mobile: MobileInterface):
    """Return the navigation Screen Object for the session's platform.

    Accepts the web platforms too: `ios-web` and `android-web` run in a browser
    on the same device family, so they take the same native chrome. The base
    platform is the part before the hyphen.

    Raises on anything unrecognised rather than guessing. A silent default here
    would pick one platform's navigation for the other and produce a failure far
    from its cause - the same reasoning as `locator()` raising on a missing key.
    """
    platform = (mobile.platform or "").lower()
    base = platform.split("-", 1)[0]
    try:
        return _BY_PLATFORM[base](mobile)
    except KeyError:
        raise ValueError(
            f"No navigation Screen Object for platform {platform!r} "
            f"(base {base!r}; known: {sorted(_BY_PLATFORM)}). Add one under "
            f"_reference/navigation/ - do not reuse another platform's."
        ) from None
