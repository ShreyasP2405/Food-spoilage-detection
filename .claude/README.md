# Session Context — Banana Storage Saver

This folder is a self-contained snapshot of the full collaboration session that built this project. Drop it in front of any new AI assistant (Claude, GPT, Gemini, Cursor, Copilot) and they'll have everything they need to continue without re-asking what's been done.

## Why this exists

You wanted to be able to continue from any account or machine. The chat transcript itself isn't portable, but the *facts* in it are. This folder captures those facts.

## What's in here

| File | Contents |
|---|---|
| `00_RESUME_PROMPT.md` | **Start here.** Paste this to a new AI assistant to brief it. |
| `01_ORIGINAL_BRIEF.md` | The user's original idea + the full Master Prompt v1 they pasted |
| `02_DECISIONS.md` | All architecture/tech-stack decisions made and *why* |
| `03_BUILD_LOG.md` | Chronological list of what was built, in what order |
| `04_PROJECT_STATE.md` | Current state of the project: what works, what doesn't, what's next |
| `05_KNOWN_ISSUES.md` | Open caveats, gotchas, follow-ups |
| `06_ENV_DETAILS.md` | OS, Docker, Python version, ports, paths — everything an assistant needs to know about the environment |
| `07_CHEATSHEET.md` | Common commands you'll need |
| `inventory.txt` | Snapshot of every file in the project at the time of this save |

## How to resume

**On a new machine / new account:**
1. Make sure this whole folder (`banana-storage-saver/`) is present.
2. Open a new chat with your AI of choice.
3. Paste the contents of `.claude/00_RESUME_PROMPT.md`.
4. Continue.

**The AI does NOT need access to the chat history** — everything load-bearing is in these files.
