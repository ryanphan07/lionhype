# Handoff: session 12 ship prep (2026-10-28)

## 1. Done
- pipeline.py: M1 sweep deletes only `<32hex>_*` videos and 32-hex audio dirs; M3 HTTP status errors say "The AI model rejected the request" (status logged); M4 run_pipeline registers its task, cancels clean up files.
- jobs.py: task handles; has_active() cancels a stale job's task (M4).
- tts.py/config.py: M2 TTS_RETRIES (1) and TTS_RETRY_DELAY_SECONDS (1.0); retries timeouts, connection errors, 5xx only, not 401/403.
- commentary.py: synthesizing progress reported per finished clip (70-90).
- Tests added: sweep survivors, retry/no-retry/auth, 5xx friendly error, stale task cancel.
- Deleted docker-compose.yml and both Dockerfiles; LICENSE (MIT) added; DECISIONS D4=A and D5 recorded.
- Docs: README, STATE, TASKS, CONVENTIONS (context paragraph rewritten), BRIEFING, OWNER_TODO; test count 105 everywhere. M5 note was already in README.

## 2. Decisions and deviations
- The prompt's placeholders were unfilled (<NAME>, <TESTED_LENGTHS>, <X>, <MODEL>, bug list). LICENSE uses "Ryan Phan" (git user). README states only measured facts (about 45 s per 10 s on Qwen3.5-9B; ~60 s supported demo); no tested lengths listed. Item 9: no bugs supplied, none fixed.

## 3. Results
- pytest (backend venv): 105 passed. Frontend lint clean, build ok. Global python lacks mutagen (1 fail there); use the venv.

## 4. Not verified
- Live LLM/TTS/browser run; real edge-tts retry behavior; stale-task cancel against a real hung job.

## 5. Open issues and risks
- README limitations lack the owner's tested clip lengths and 35B speed (tts.py retry list is a guess at edge-tts error types).

## 6. Suggested next session
Owner live run, send numbers and bugs; then fill README limitations, GIF, tag v0.1.0.
