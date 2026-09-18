"""
Reference Implementation - Canonical code patterns for AI to learn from.

AI MUST read these files before generating any layer code:
- screens/*.py    -> Screen Object patterns (locators, atomic methods, state methods)
- tasks/*.py      -> Task patterns (@autologger, Screen composition, no returns)
- roles/*.py      -> Role patterns (@autologger, Task composition, workflows)
- tests/*.py      -> Test patterns (fixtures, Role calls, Screen assertions)

Locators are platform-keyed dicts, and every value must appear verbatim in a
committed capture under _captures/. See README.md for full documentation.
"""
