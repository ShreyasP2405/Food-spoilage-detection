# RESUME PROMPT — paste this to a new AI assistant to continue this project

---

I'm continuing work on a project called **Banana Storage Saver**. It is software-only (so far) and predicts the Remaining Shelf Life (RSL) in days for stored Cavendish bananas from temperature, humidity, and gas readings.

## Read these files BEFORE doing anything

The full session context is captured in this folder:

```
banana-storage-saver/.claude/
├── 00_RESUME_PROMPT.md   ← you're reading this
├── 01_ORIGINAL_BRIEF.md  ← my original idea + the master prompt that built v1
├── 02_DECISIONS.md       ← every architecture/tech decision and why
├── 03_BUILD_LOG.md       ← chronological build order
├── 04_PROJECT_STATE.md   ← what's running, verified metrics, what works
├── 05_KNOWN_ISSUES.md    ← open caveats, do not "fix" these silently
├── 06_ENV_DETAILS.md     ← OS, Docker, Python, ports, paths
├── 07_CHEATSHEET.md      ← common commands
└── inventory.txt         ← every file at session-save time
```

Plus the formal docs in `docs/`:

```
docs/
├── PROFESSOR_GUIDE.md    ← the complete walkthrough I show my professor
├── SCIENCE.md            ← cited equations and constants
├── ARCHITECTURE.md       ← layer diagram + data flow
├── API.md                ← endpoint contracts
└── EXTENDING.md          ← multi-commodity recipe
```

**Ground rules for the new assistant:**

1. **Don't re-derive what's already decided.** Read `02_DECISIONS.md` first.
2. **Don't "fix" the known issues** in `05_KNOWN_ISSUES.md` without asking — they're known and intentional in some cases.
3. **Use Docker for everything.** No host venv. No host pip install. The user is on Windows and prefers everything containerized. Confirmed in `06_ENV_DETAILS.md`.
4. **Don't pretend to have access to the previous chat** — work entirely from these files.
5. **Don't add features I didn't ask for.** Auth, multi-tenancy, cloud deploy etc. are explicitly out of scope.
6. **Be honest about scope** — this is a banana-only MVP trained on physics-simulated data. Real-sensor validation is future work. README says so. Don't overclaim.

## What I might ask you to do next (likely tasks)

- Improve the dataset balance (the on_time_warning_rate is 0.0 — see `05_KNOWN_ISSUES.md` for the root cause).
- Add a CSV upload + retrain feature (currently we only have CSV upload + predict).
- Add a second commodity (rice / mango / wheat) per `docs/EXTENDING.md`.
- Wire real ESP32 hardware via `backend/app/data_source/mqtt_stub.py`.
- Add user-facing alerts (webhooks, email, SMS).
- Field-validate against real banana data once collected.

When I tell you what to do, *first confirm you've read the context*, then propose a brief plan, then execute it inside Docker. Use `Edit`/`Write`/`Bash` tools as appropriate.

## How I work with you

- I'm on Windows 11, working in `c:\Users\rachi\OneDrive\Desktop\shreyas\banana-storage-saver\`
- I prefer terse responses. Short sentences. No fluff. State results, not deliberation.
- I don't want comments scattered through code unless the WHY is non-obvious.
- I want honest "this won't work because X" pushback, not sycophantic agreement.
- For risky/destructive actions: ask first.

That's the brief. Read the files in `.session-context/`, confirm you understand, then ask what I want to work on next.
