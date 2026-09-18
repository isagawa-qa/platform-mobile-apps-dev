# platform-mobile-apps-dev

Development repo for the Isagawa mobile QA platform (iOS + Android, Appium, 5-layer architecture). Work happens here until the approach is proven; `isagawa-qa/platform-mobile-apps` is created from the finished tree afterwards.

Public on purpose: GitHub's standard hosted runners, including macOS, are free on public repositories, which is what lets iOS tests run without a Mac. Nothing client-owned, and no credentials, belong in this repo.

## Current state

Proof of concept only. `.github/workflows/ios-poc.yml` boots an iOS Simulator on a `macos-15` runner, installs Appium 3.7.0 with the XCUITest driver 12.12.4, downloads the Sauce Labs My Demo App simulator build, and runs `tests/test_ios_smoke.py`: a session starts, the app reaches the foreground, and the XCUITest UI tree comes back. Screenshot and page source upload as artifacts.

The framework itself is not here yet. It gets copied from `isagawa-qa/platform-selenium` (`origin/main`) and adapted, 40 files unchanged and 46 changed, per `projects/platform-mobile-apps/template-file-map.md` in the sr-dev-workspace.

## Research

`projects/platform-mobile-apps/` in the sr-dev-workspace (backlog 318): stack pins, the iOS-from-Windows routes, the app-type coverage matrix, the reference app choice, and the open owner decisions.
