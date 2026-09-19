# /kernel/session-start

Check state and resume if needed. Always invoke first.

## Instructions

1. **Check for existing state:**
   - Read `.claude/state/session_state.json` if exists
   - If `needs_restart` is true, resume from `resume_after_restart`

2. **Check for domain state:**
   - Look for `.claude/state/[domain]_workflow.json`
   - If exists, summarize current progress

3. **Domain persistence rule (CRITICAL):**
   - **If domain exists → USE IT** (never create new)
   - One project = one domain = one protocol
   - New capabilities (API, UI, etc.) extend existing protocol via `/kernel/learn`
   - Only invoke `/kernel/domain-setup` if NO domain exists at all

4. **Update session state:**
   ```json
   {
     "session_started": true,
     "timestamp": "...",
     "resumed_from": null | "previous_step"
   }
   ```

5. **Load protocol context (do NOT force an anchor):**

   Read, with the Read tool:
   - `.claude/protocols/[domain]-protocol.md` and every reference it indexes
   - `.claude/lessons/lessons.md`

   Summarise the architecture patterns, naming conventions, quality gates and
   anti-patterns that bear on the work ahead.

   **Do NOT set `anchored: false`.** The action counter is the ONLY anchor
   trigger. Forcing an anchor at session start was a second trigger for one
   control, and drift accumulates with actions rather than with session
   boundaries - a session that does three things does not need a re-centre
   before doing them. Reading protocol and lessons HERE is what that forced
   anchor was really for, and this gets it without spending an anchor cycle.

   The hook blocks for an anchor when the counter passes `actions_limit`, and
   issues a token with it. That is the only time to invoke `/kernel/anchor`.

6. **Report and PROCEED (no asking):**
   ```
   Session started.
   - State: [fresh | resumed from X]
   - Domain: [none | domain name]
   - Next: [what happens next]

   Proceeding.
   ```

7. **Auto-proceed (MANDATORY — do NOT ask the user):**

   After reporting, IMMEDIATELY proceed to the next step:

   - **No domain exists** → Invoke `/kernel/domain-setup` NOW
   - **Domain exists** → Invoke `/kernel/anchor` NOW
   - **Resuming from restart** → Follow resume instructions (step 1)

   **NEVER ask "Would you like me to..." or "Should I...".**
   The kernel is autonomous. Report what you're doing, then do it.

## State File Location

`.claude/state/session_state.json`
