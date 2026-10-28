# Handoff: owner checklist and planning briefing (2026-10-28)

## 1. Done
- docs/OWNER_TODO.md (new): decisions, CLAUDE.md edits, live-session checklist with commands, ship steps.
- docs/BRIEFING.md (new): self-contained summary for the planning chat, with session prompts and resume guardrails.
- TASKS, README and CONVENTIONS point to them; CONVENTIONS says to refresh BRIEFING.md when state or roadmap change.
- No source code changed.

## 2. Decisions and deviations
- Nothing decided for the owner; D4, LICENSE, Docker and the CLAUDE.md edits are listed in OWNER_TODO.

## 3. Results
- Docs only. Last checks: pytest 101 passed, lint clean, build ok, npm audit 0.

## 4. Not verified, needs manual testing
- Live LLM + TTS + browser run (OWNER_TODO section C).

## 5. Open issues and risks
- pipeline.py sweep_uploads can delete a wrong folder if UPLOAD_DIR is customized (M1).
- tts.py has no retry (M2); friendly_error mislabels HTTP errors (M3); a stale job's task is not cancelled (M4).

## 6. Suggested next session
Session 12 in TASKS.md (prompt in BRIEFING.md), then the owner's live session.
